#!/usr/bin/env python3
"""
CDK Application entry point for AWSomeBuilder.

This file defines the main CDK application and applies mandatory
tagging aspects to ensure all AWS resources are properly tagged.

"""

import os
import json
import logging

import aws_cdk as cdk
import cdk_nag as nag
from aws_cdk import Aspects

from infrastructure.stacks.assistant_stack import AssistantStack
from infrastructure.stacks.document_workflow_stack import DocumentWorkflowStack
from infrastructure.stacks.backend_stack import BackendStack
from infrastructure.stacks.api_stack import ApiStack

from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

config_path = Path("config/config.json")

if config_path.exists():
    logger.info("Using production configuration from config/config.json")
    # Load configuration
    with open(config_path, "r") as f:
        config = json.load(f)
else:
    logger.warning("Configuration file not found, using default configuration")
    config = {}

app = cdk.App()

# Create environment configuration
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT", config.get("account")),
    region=os.getenv("CDK_DEFAULT_REGION", config.get("region")),
)

# Load mandatory tags and apply them to the app
logger.info("Loading mandatory tags from config/tags.json")
with open("config/tags.json", "r") as f:
    tags_config = json.load(f)
    mandatory_tags = tags_config.get("mandatory_tags", {})

# Apply mandatory tags to all resources in the app
for tag_key, tag_value in mandatory_tags.items():
    cdk.Tags.of(app).add(tag_key, tag_value)
logger.info(f"Applied {len(mandatory_tags)} mandatory tags to all resources")
# Add CDK Nag checks based on configuration
logger.info("Configuring CDK Nag security checks...")


def add_nag_check_safely(check_name, check_class_name, enabled):
    """Safely add a CDK Nag check following AWS CDK aspects pattern"""
    if not enabled:
        logger.info(f"{check_name} disabled")
        return False

    try:
        # Check if the class exists in cdk_nag module
        if not hasattr(nag, check_class_name):
            logger.warning(
                f"{check_name} class '{check_class_name}' not found in cdk-nag"
            )
            return False

        # Get the class and instantiate it
        check_class = getattr(nag, check_class_name)
        check_instance = check_class()

        # Verify it has the visit method (proper aspect interface)
        if not hasattr(check_instance, "visit"):
            logger.warning(
                f"{check_name} does not implement proper aspect interface (missing visit method)"
            )
            return False

        # Add the aspect to the app
        Aspects.of(app).add(check_instance)
        logger.info(f"Successfully enabled {check_name}")
        return True

    except Exception as e:
        logger.warning(f"Error enabling {check_name}: {str(e)}")
        logger.debug(
            f"Full error details for {check_name}: {e}", exc_info=True)
        return False


# Apply CDK Nag checks based on configuration
nag_results = {}

# AWS Solutions Checks (most common)
nag_results["aws_solutions"] = add_nag_check_safely(
    "AWS Solutions checks",
    "AwsSolutionsChecks",
    config.get("enableAWSSolutionsChecks", False),
)

# HIPAA Security Checks (try different possible names)
hipaa_enabled = config.get("enableHIPAAChecks", False)
if hipaa_enabled:
    # Try the most common class names for HIPAA checks
    hipaa_success = add_nag_check_safely(
        "HIPAA security checks", "HipaaSecurityChecks", True
    ) or add_nag_check_safely("HIPAA security checks", "HIPAASecurityChecks", True)
    nag_results["hipaa"] = hipaa_success
    if not hipaa_success:
        logger.warning(
            "HIPAA security checks requested but no compatible class found")
else:
    logger.info("HIPAA security checks disabled")
    nag_results["hipaa"] = False

# Serverless Checks
nag_results["serverless"] = add_nag_check_safely(
    "Serverless checks", "ServerlessChecks", config.get(
        "enableServerlessChecks", False)
)

# Nag Suppressions
nag_results["suppressions"] = add_nag_check_safely(
    "Nag suppressions", "NagSuppressions", config.get(
        "enableNagSuppressions", False)
)

# Log summary
enabled_nag_checks = [name for name, success in nag_results.items() if success]
if enabled_nag_checks:
    logger.info(
        f"CDK Nag checks successfully enabled: {', '.join(enabled_nag_checks)}")
else:
    logger.info("No CDK Nag checks enabled")


logger.info("Creating CDK stacks...")

# Create the document workflow stack first (provides raw bucket)
document_workflow_stack = DocumentWorkflowStack(
    app,
    "documentstack",
    env=env,
    stack_name="AWSomeBuilder2-DocumentWorkflowStack",
    description="Workflow de procesamiento de documentos",
)

# Create the backend stack (database only)
backend_stack = BackendStack(
    app,
    "backendstack",
    env=env,
    stack_name="AWSomeBuilder2-BackendStack",
    description="Database infrastructure for healthcare system",
)

# Create the API stack
api_stack = ApiStack(
    app,
    "apistack",
    env=env,
    stack_name="AWSomeBuilder2-ApiStack",
    description="API Gateway and Lambda functions for healthcare system",
)

# Create the assistant stack
assistant_stack = AssistantStack(
    app,
    "genaistack",
    processed_bucket=document_workflow_stack.processed_bucket,
    database_cluster=backend_stack.db_cluster,
    env=env,
    stack_name="AWSomeBuilder2-VirtualAssistantStack",
    description="Asistente virtual con GenAI",
)

# Add stack dependencies
logger.info("Configuring stack dependencies...")
backend_stack.add_dependency(document_workflow_stack)
assistant_stack.add_dependency(backend_stack)
logger.info("Stack dependencies configured successfully")

logger.info("Starting CDK synthesis...")
app.synth()
logger.info("CDK synthesis completed successfully")

logger.warning("⚠️ Heads up! the frontend need to be deployed separeately using Amplify!")
