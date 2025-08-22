#!/usr/bin/env python3
"""
CDK Application entry point for AWSomeBuilder 2.

This file defines the main CDK application and applies mandatory
tagging aspects to ensure all AWS resources are properly tagged.
"""

import os
import json

import aws_cdk as cdk
import cdk_nag as nag
from aws_cdk import Aspects

from infrastructure.stacks.assistant_stack import AssistantStack
from infrastructure.stacks.document_workflow_stack import DocumentWorkflowStack
from infrastructure.stacks.backend_stack import BackendStack
from infrastructure.stacks.frontend_stack import FrontendStack

from pathlib import Path

config_path = Path("config/prod_config.json")

if config_path.exists():
    print("Using prod configuration")
    # Load configuration
    with open(config_path, "r") as f:
        config = json.load(f)
else:
    print("Using default configuration")
    config = {}

app = cdk.App()

# Create environment configuration
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT", config.get("account")),
    region=os.getenv("CDK_DEFAULT_REGION", config.get("region")),
)

# Load mandatory tags and apply them to the app
with open("config/tags.json", "r") as f:
    tags_config = json.load(f)
    mandatory_tags = tags_config.get("mandatory_tags", {})

# Apply mandatory tags to all resources in the app
for tag_key, tag_value in mandatory_tags.items():
    cdk.Tags.of(app).add(tag_key, tag_value)
# Add CDK Nag checks
# Rules will be re-enabled during compliance review
# TODO Un comment-out
# Aspects.of(app).add(nag.AwsSolutionsChecks())
# Aspects.of(app).add(nag.ServerlessChecks())
# Aspects.of(app).add(nag.HIPAASecurityChecks())


# Create the main stacks
backend_stack = BackendStack(
    app,
    "backendstack",
    env=env,
    stack_name="AWSomeBuilder2-BackendStack",
    description="API Backend para las funcionalidades del asistente",
)


document_workflow_stack = DocumentWorkflowStack(
    app,
    "documentstack",
    env=env,
    stack_name="AWSomeBuilder2-DocumentWorkflowStack",
    description="Workflow de procesamiento de documentos",
)


assistant_stack = AssistantStack(
    app,
    "genaistack",
    env=env,
    stack_name="AWSomeBuilder2-VirtualAssistantStack",
    description="Asistente virtual con GenAI",
)

frontend_stack = FrontendStack(
    app,
    "frontendstack",
    env=env,
    stack_name="AWSomeBuilder2-FrontendStack",
    description="Frontend React para el asistente virtual de HealthCare",
)

# Add stack dependencies
backend_stack.add_dependency(document_workflow_stack)
assistant_stack.add_dependency(backend_stack)
frontend_stack.add_dependency(assistant_stack)

app.synth()
