"""
Bedrock Guardrail Construct for Healthcare Workflow System.
"""

from aws_cdk import aws_bedrock as bedrock
from constructs import Construct


class BedrockGuardrailConstruct(Construct):
    """
    Construct for creating Bedrock Guardrails with healthcare-specific configurations.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.guardrails = bedrock.CfnGuardrail(
            self,
            "HealthCareGuardRails",
            blocked_input_messaging="Lo siento, pero tu mensaje contiene información no permitida",
            blocked_outputs_messaging="Respuesta bloqueada por Bedrock Guardrails",
            name="HealthCareGuardRails",
            automated_reasoning_policy_config=None,
            content_policy_config=bedrock.CfnGuardrail.ContentPolicyConfigProperty(
                filters_config=[
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="MEDIUM",
                        output_strength="MEDIUM",
                        type="HATE",
                        input_action="BLOCK",
                        input_enabled=True,
                        input_modalities=["TEXT", "IMAGE"],
                        output_action="BLOCK",
                        output_enabled=True,
                        output_modalities=["TEXT"]
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="MEDIUM",
                        output_strength="MEDIUM",
                        type="INSULTS",
                        input_action="BLOCK",
                        input_enabled=True,
                        input_modalities=["TEXT", "IMAGE"],
                        output_action="BLOCK",
                        output_enabled=True,
                        output_modalities=["TEXT"]
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="LOW",
                        output_strength="NONE",
                        type="VIOLENCE",
                        input_action="NONE",
                        input_enabled=True,
                        input_modalities=["TEXT", "IMAGE"],
                        output_action="NONE",
                        output_enabled=False,
                        output_modalities=["TEXT"]
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="LOW",
                        output_strength="NONE",
                        type="SEXUAL",
                        input_action="NONE",
                        input_enabled=True,
                        input_modalities=["TEXT", "IMAGE"],
                        output_action="NONE",
                        output_enabled=False,
                        output_modalities=["TEXT"]
                    )
                ],
                content_filters_tier_config=bedrock.CfnGuardrail.ContentFiltersTierConfigProperty(
                    tier_name="STANDARD"
                )
            ),
            contextual_grounding_policy_config=bedrock.CfnGuardrail.ContextualGroundingPolicyConfigProperty(
                filters_config=[
                    bedrock.CfnGuardrail.ContextualGroundingFilterConfigProperty(
                        threshold=0.8,
                        type="GROUNDING"
                    ),
                    bedrock.CfnGuardrail.ContextualGroundingFilterConfigProperty(
                        threshold=0.8,
                        type="RELEVANCE"
                    )
                ]
            ),
            cross_region_config=bedrock.CfnGuardrail.GuardrailCrossRegionConfigProperty(
                guardrail_profile_arn=f"arn:aws:bedrock:{self.region}:{self.account}:guardrail-profile/us.guardrail.v1:0"
            ),
            description="Guardrails for the healthcare assistant",
            sensitive_information_policy_config=self._create_sensitive_information_policy()
        )

        self.guardrail_version = bedrock.CfnGuardrailVersion(
            self, "GuardrailVersion",
            guardrail_identifier=self.guardrails.attr_guardrail_id
        )

    def _create_sensitive_information_policy(self) -> bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty:
        """
        Create sensitive information policy with PII entities and LATAM-specific regex patterns.
        """
        return bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty(
            pii_entities_config=[
                # NAME - Allow input and output for patient identification
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="NAME",
                    action="NONE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="NONE",
                    output_enabled=True
                ),
                # AGE - Allow input, anonymize output
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="AGE",
                    action="NONE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="NONE",
                    output_enabled=True
                ),
                # ADDRESS - Allow input, anonymize output
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="ADDRESS",
                    action="NONE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="NONE",
                    output_enabled=True
                ),
                # EMAIL - Allow input, anonymize output
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="EMAIL",
                    action="ANONYMIZE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="ANONYMIZE",
                    output_enabled=True
                ),
                # PHONE - Allow input, anonymize output (will catch LATAM formats)
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="PHONE",
                    action="ANONYMIZE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="ANONYMIZE",
                    output_enabled=True
                ),
                # CREDIT_DEBIT_CARD_NUMBER - For billing/insurance
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="CREDIT_DEBIT_CARD_NUMBER",
                    action="ANONYMIZE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="ANONYMIZE",
                    output_enabled=True
                )
            ],
            regexes_config=self._create_latam_regex_patterns()
        )

    def _create_latam_regex_patterns(self) -> list:
        """
        Create LATAM-specific regex patterns for healthcare data protection.
        """
        return [
            # Cédula de Ciudadanía Colombia (8-10 digits)
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="CedulaColombia",
                description="Cédula de Ciudadanía Colombia",
                pattern=r"\b\d{8,10}\b",
                action="NONE",
                input_action="NONE",
                input_enabled=True,
                output_action="NONE",
                output_enabled=True
            ),
            # RUT Chile (XX.XXX.XXX-X format)
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="RutChile",
                description="RUT Chile format",
                pattern=r"\b\d{1,2}\.\d{3}\.\d{3}-[\dkK]\b",
                action="NONE",
                input_action="NONE",
                input_enabled=True,
                output_action="NONE",
                output_enabled=True
            ),
            # DNI Argentina (8 digits)
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="DniArgentina",
                description="DNI Argentina",
                pattern=r"\bDNI\s*:?\s*\d{8}\b",
                action="NONE",
                input_action="NONE",
                input_enabled=True,
                output_action="NONE",
                output_enabled=True
            ),
            # CPF Brasil (XXX.XXX.XXX-XX format)
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="CpfBrasil",
                description="CPF Brasil format",
                pattern=r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
                action="NONE",
                input_action="NONE",
                input_enabled=True,
                output_action="NONE",
                output_enabled=True
            ),
            # Cédula Ecuador (10 digits)
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="CedulaEcuador",
                description="Cédula Ecuador",
                pattern=r"\b\d{10}\b",
                action="NONE",
                input_action="NONE",
                input_enabled=True,
                output_action="NONE",
                output_enabled=True
            ),
            # LATAM Phone Numbers (various formats)
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="TelefonoLatam",
                description="Números telefónicos LATAM",
                pattern=r"\b(?:\+?[1-9]\d{1,3}[-.\s]?)?\(?[1-9]\d{2,3}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b",
                action="ANONYMIZE",
                input_action="NONE",
                input_enabled=True,
                output_action="ANONYMIZE",
                output_enabled=True
            ),
            # Número de Historia Clínica (Medical Record)
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="HistoriaClinica",
                description="Número de Historia Clínica",
                pattern=r"\b(?:HC|Historia|Expediente)\s*:?\s*\d{6,10}\b",
                action="ANONYMIZE",
                input_action="NONE",
                input_enabled=True,
                output_action="ANONYMIZE",
                output_enabled=True
            ),
            # Número de Seguro Social LATAM
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="SeguroSocialLatam",
                description="Número de Seguro Social LATAM",
                pattern=r"\b(?:EPS|ISSS|IMSS|Seguro)\s*:?\s*\d{8,12}\b",
                action="ANONYMIZE",
                input_action="NONE",
                input_enabled=True,
                output_action="ANONYMIZE",
                output_enabled=True
            )
        ]

    @property
    def guardrail_id(self) -> str:
        """Return the guardrail ID."""
        return self.guardrails.attr_guardrail_id

    @property
    def guardrail_version_id(self) -> str:
        """Return the guardrail version ID."""
        return self.guardrail_version.attr_version

    @property
    def region(self) -> str:
        """Return the current region."""
        from aws_cdk import Stack
        return Stack.of(self).region

    @property
    def account(self) -> str:
        """Return the current account."""
        from aws_cdk import Stack
        return Stack.of(self).account
