"""
Guardrail Monitoring Hook for Healthcare Agent.

This hook implements shadow-mode guardrail monitoring using Bedrock's ApplyGuardrail API.
It tracks when guardrails would be triggered without actually blocking content,
enabling monitoring and tuning before enforcement.

Key Features:
- Non-blocking monitoring (shadow mode)
- Detailed violation logging for CloudWatch
- Separate input/output evaluation
- Healthcare-specific PII tracking
- Integration with AgentCore observability
"""

import logging
import boto3
from typing import Dict, Any, List, Optional
from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent, AfterInvocationEvent

logger = logging.getLogger("healthcare_agent.guardrail_monitoring")


class GuardrailMonitoringHook(HookProvider):
    """
    Hook for monitoring guardrail violations in shadow mode.
    
    This hook evaluates content using Bedrock's ApplyGuardrail API without blocking,
    allowing you to track violations and tune guardrails before enforcement.
    """

    def __init__(
        self,
        guardrail_id: str,
        guardrail_version: str,
        aws_region: str = "us-east-1",
        session_id: Optional[str] = None
    ):
        """
        Initialize the guardrail monitoring hook.

        Args:
            guardrail_id: Bedrock guardrail identifier
            guardrail_version: Guardrail version to use
            aws_region: AWS region for Bedrock client
            session_id: Optional session ID for logging context
        """
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self.aws_region = aws_region
        self.session_id = session_id or "unknown"
        
        # Initialize Bedrock client
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=aws_region
        )
        
        # Track interventions for this session
        self.interventions: List[Dict[str, Any]] = []
        
        logger.info(
            f"🛡️ Guardrail monitoring initialized | "
            f"guardrail_id={guardrail_id} | "
            f"version={guardrail_version} | "
            f"region={aws_region}"
        )

    def register_hooks(self, registry: HookRegistry) -> None:
        """
        Register hook callbacks with the agent.

        Args:
            registry: Hook registry to register callbacks with
        """
        # Check user input before model invocation
        registry.add_callback(MessageAddedEvent, self.check_message)
        
        # Check assistant response after model invocation
        registry.add_callback(AfterInvocationEvent, self.check_message)
        
        logger.info("✅ Guardrail monitoring hooks registered")

    def evaluate_content(
        self,
        content: str,
        source: str = "INPUT"
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate content using Bedrock ApplyGuardrail API in shadow mode.

        Args:
            content: Text content to evaluate
            source: Content source ("INPUT" or "OUTPUT")

        Returns:
            Guardrail evaluation result or None if evaluation fails
        """
        if not content or not content.strip():
            logger.debug(f"⏭️ Skipping empty content evaluation | source={source}")
            return None

        try:
            # Call Bedrock ApplyGuardrail API
            response = self.bedrock_client.apply_guardrail(
                guardrailIdentifier=self.guardrail_id,
                guardrailVersion=self.guardrail_version,
                source=source,
                content=[{"text": {"text": content}}]
            )

            action = response.get("action")
            assessments = response.get("assessments", [])
            
            # Check if there are any assessments (detections) even if action is NONE
            has_detections = any(
                assessment for assessment in assessments
                if any(key in assessment for key in ["topicPolicy", "contentPolicy", "sensitiveInformationPolicy", "contextualGroundingPolicy"])
            )
            
            # Log and store if guardrail intervened OR detected issues (even without intervention)
            if action == "GUARDRAIL_INTERVENED" or has_detections:
                intervention_data = self._log_intervention(content, source, response)
                self.interventions.append(intervention_data)
            else:
                logger.debug(
                    f"✅ Content passed guardrail check | "
                    f"source={source} | "
                    f"length={len(content)} | "
                    f"session_id={self.session_id}"
                )
            
            return response

        except Exception as e:
            logger.error(
                f"❌ Guardrail evaluation failed | "
                f"source={source} | "
                f"error={str(e)} | "
                f"session_id={self.session_id}"
            )
            return None

    def _log_intervention(
        self,
        content: str,
        source: str,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Log detailed information about guardrail intervention and return structured data.

        Args:
            content: Content that triggered intervention
            source: Content source ("INPUT" or "OUTPUT")
            response: Guardrail API response

        Returns:
            Structured intervention data
        """
        # Determine log level and message based on action
        action = response.get("action")
        if action == "GUARDRAIL_INTERVENED":
            logger.warning(
                f"🚨 GUARDRAIL WOULD BLOCK | "
                f"source={source} | "
                f"content_preview={content[:100]}... | "
                f"session_id={self.session_id}"
            )
        else:
            logger.info(
                f"👀 GUARDRAIL DETECTED (no intervention) | "
                f"source={source} | "
                f"content_preview={content[:100]}... | "
                f"session_id={self.session_id}"
            )

        # Build structured intervention data
        intervention_data = {
            "source": source,
            "action": action,
            "content_preview": content[:100],
            "timestamp": response.get("timestamp"),
            "violations": []
        }

        # Parse and log detailed assessments
        assessments = response.get("assessments", [])
        
        for assessment in assessments:
            # Topic Policy violations
            if "topicPolicy" in assessment:
                violations = self._log_topic_violations(assessment["topicPolicy"], source)
                if violations:
                    intervention_data["violations"].extend(violations)
            
            # Content Policy violations
            if "contentPolicy" in assessment:
                violations = self._log_content_violations(assessment["contentPolicy"], source)
                if violations:
                    intervention_data["violations"].extend(violations)
            
            # Sensitive Information violations
            if "sensitiveInformationPolicy" in assessment:
                violations = self._log_pii_violations(assessment["sensitiveInformationPolicy"], source)
                if violations:
                    intervention_data["violations"].extend(violations)
            
            # Contextual Grounding violations
            if "contextualGroundingPolicy" in assessment:
                violations = self._log_grounding_violations(assessment["contextualGroundingPolicy"], source)
                if violations:
                    intervention_data["violations"].extend(violations)

        return intervention_data

    def _log_topic_violations(
        self,
        topic_policy: Dict[str, Any],
        source: str
    ) -> List[Dict[str, Any]]:
        """Log topic policy violations and return structured data."""
        topics = topic_policy.get("topics", [])
        violations = []
        
        for topic in topics:
            violation = {
                "type": "topic_policy",
                "topic": topic.get("name"),
                "action": topic.get("action"),
                "policy_type": topic.get("type")
            }
            violations.append(violation)
            
            logger.warning(
                f"🚫 Topic Policy Violation | "
                f"source={source} | "
                f"topic={topic.get('name')} | "
                f"action={topic.get('action')} | "
                f"type={topic.get('type')} | "
                f"session_id={self.session_id}"
            )
        
        return violations

    def _log_content_violations(
        self,
        content_policy: Dict[str, Any],
        source: str
    ) -> List[Dict[str, Any]]:
        """Log content policy violations and return structured data."""
        filters = content_policy.get("filters", [])
        violations = []
        
        for filter_item in filters:
            violation = {
                "type": "content_policy",
                "content_type": filter_item.get("type"),
                "confidence": filter_item.get("confidence"),
                "action": filter_item.get("action")
            }
            violations.append(violation)
            
            logger.warning(
                f"⚠️ Content Policy Violation | "
                f"source={source} | "
                f"type={filter_item.get('type')} | "
                f"confidence={filter_item.get('confidence')} | "
                f"action={filter_item.get('action')} | "
                f"session_id={self.session_id}"
            )
        
        return violations

    def _log_pii_violations(
        self,
        pii_policy: Dict[str, Any],
        source: str
    ) -> List[Dict[str, Any]]:
        """Log sensitive information (PII) violations and return structured data."""
        pii_entities = pii_policy.get("piiEntities", [])
        regexes = pii_policy.get("regexes", [])
        violations = []
        
        # Log PII entity detections
        for entity in pii_entities:
            violation = {
                "type": "pii_entity",
                "pii_type": entity.get("type"),
                "action": entity.get("action")
            }
            violations.append(violation)
            
            logger.warning(
                f"🔒 PII Detected | "
                f"source={source} | "
                f"type={entity.get('type')} | "
                f"action={entity.get('action')} | "
                f"session_id={self.session_id}"
            )
        
        # Log regex pattern matches (healthcare-specific)
        for regex in regexes:
            violation = {
                "type": "pii_regex",
                "pattern": regex.get("name"),
                "action": regex.get("action")
            }
            violations.append(violation)
            
            logger.warning(
                f"🏥 Healthcare PII Detected | "
                f"source={source} | "
                f"pattern={regex.get('name')} | "
                f"action={regex.get('action')} | "
                f"session_id={self.session_id}"
            )
        
        return violations

    def _log_grounding_violations(
        self,
        grounding_policy: Dict[str, Any],
        source: str
    ) -> List[Dict[str, Any]]:
        """Log contextual grounding violations and return structured data."""
        filters = grounding_policy.get("filters", [])
        violations = []
        
        for filter_item in filters:
            violation = {
                "type": "grounding_policy",
                "grounding_type": filter_item.get("type"),
                "score": filter_item.get("score"),
                "threshold": filter_item.get("threshold"),
                "action": filter_item.get("action")
            }
            violations.append(violation)
            
            logger.warning(
                f"📊 Grounding Violation | "
                f"source={source} | "
                f"type={filter_item.get('type')} | "
                f"score={filter_item.get('score')} | "
                f"threshold={filter_item.get('threshold')} | "
                f"action={filter_item.get('action')} | "
                f"session_id={self.session_id}"
            )
        
        return violations

    def check_message(self, event) -> None:
        """
        Unified message checker for both user input and assistant responses.

        Args:
            event: Either MessageAddedEvent or AfterInvocationEvent from Strands
        """
        # Determine message and source based on event type
        if isinstance(event, MessageAddedEvent):
            message = event.message
            source = "INPUT" if message.get("role") == "user" else None
                
        elif isinstance(event, AfterInvocationEvent):
            if not event.agent.messages:
                return
            message = event.agent.messages[-1]
            source = "OUTPUT" if message.get("role") == "assistant" else None
            
            # Store accumulated interventions in agent state after processing OUTPUT
            # This captures ALL interventions across the entire conversation
            if source == "OUTPUT":
                event.agent.state.set("guardrail_interventions", self.interventions)
                logger.debug(
                    f"💾 Stored {len(self.interventions)} total intervention(s) in agent state | "
                    f"session_id={self.session_id}"
                )
        else:
            return

        # Skip if not a relevant role
        if not source:
            return

        # Extract text content from message
        content = self._extract_text_from_message(message)
        
        if content:
            logger.debug(
                f"🔍 Evaluating {source.lower()} | "
                f"length={len(content)} | "
                f"session_id={self.session_id}"
            )
            self.evaluate_content(content, source)

    def _extract_text_from_message(self, message: Dict[str, Any]) -> str:
        """
        Extract text content from a Strands message.

        Args:
            message: Strands message object

        Returns:
            Combined text content
        """
        content_blocks = message.get("content", [])
        text_parts = []

        for block in content_blocks:
            # Extract text from text blocks
            if isinstance(block, dict) and "text" in block:
                text_parts.append(block["text"])
            # Handle string content blocks
            elif isinstance(block, str):
                text_parts.append(block)

        return "\n".join(text_parts)


def create_guardrail_monitoring_hook(
    guardrail_id: str,
    guardrail_version: str,
    aws_region: str = "us-east-1",
    session_id: Optional[str] = None
) -> GuardrailMonitoringHook:
    """
    Factory function to create a guardrail monitoring hook.

    Args:
        guardrail_id: Bedrock guardrail identifier
        guardrail_version: Guardrail version to use
        aws_region: AWS region for Bedrock client
        session_id: Optional session ID for logging context

    Returns:
        Configured GuardrailMonitoringHook instance
    """
    return GuardrailMonitoringHook(
        guardrail_id=guardrail_id,
        guardrail_version=guardrail_version,
        aws_region=aws_region,
        session_id=session_id
    )
