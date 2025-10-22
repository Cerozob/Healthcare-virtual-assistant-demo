"""
CDK Construct for managing Bedrock Data Automation blueprints.
"""

import json
from pathlib import Path
from typing import Dict, List
from aws_cdk import Stack
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_iam as iam
from constructs import Construct


class BDABlueprintsConstruct(Construct):
    """
    Construct for creating and managing BDA blueprints from JSON definitions.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load and create blueprints
        self.blueprints = self._create_blueprints()
        self.project = self.create_data_automation_project()

    def _create_blueprints(self) -> None:
        """
        Create BDA blueprints from JSON definitions.
        """
        blueprints_dir = Path(__file__).parent / "blueprints"

        blueprint_files = {
            "document": "medical-record-blueprint.json",
            "image": "medical-image-blueprint.json",
            "audio": "medical-audio-blueprint.json",
            "video": "medical-video-blueprint.json"
        }

        blueprints = {}

        for blueprint_type, filename in blueprint_files.items():
            blueprint_path = blueprints_dir / filename

            if blueprint_path.exists():
                with blueprint_path.open('r', encoding='utf-8') as f:
                    blueprint_config = json.load(f)

                # Create the blueprint
                blueprint = self._create_blueprint(
                    blueprint_type, blueprint_config)
                blueprints[blueprint_type] = blueprint

        return blueprints

    def _create_blueprint(self, blueprint_type: str, config: Dict) -> bedrock.CfnBlueprint:
        """
        Create a single BDA blueprint from configuration.

        Args:
            blueprint_type: Type identifier for the blueprint
            config: Blueprint configuration dictionary

        Returns:
            Created blueprint resource
        """
        # Create the blueprint using the correct CDK syntax
        blueprint = bedrock.CfnBlueprint(
            self,
            f"{blueprint_type.title()}Blueprint",
            blueprint_name=blueprint_type,
            schema=config,  # Pass the entire config as schema
            type=blueprint_type.upper(),  # Default type for medical documents
            tags=[
                {
                    "key": "BlueprintType",
                    "value": blueprint_type
                },
                {
                    "key": "Environment",
                    "value": "healthcare"
                }
            ]
        )

        return blueprint

    def create_data_automation_project(self, project_name: str = "healthcare-bda") -> bedrock.CfnDataAutomationProject:
        """
        Create a data automation project with custom output configuration using all blueprints.

        Args:
            project_name: Name for the project

        Returns:
            Created project resource
        """
        # Create blueprint items for custom output configuration
        blueprint_items = []
        for blueprint in self.blueprints.values():
            blueprint_arn = blueprint.attr_blueprint_arn
            blueprint_items.append(
                bedrock.CfnDataAutomationProject.BlueprintItemProperty(
                    blueprint_arn=blueprint_arn
                )
            )

        # Configure standard output settings for all media types
        standard_output_configuration = bedrock.CfnDataAutomationProject.StandardOutputConfigurationProperty(
            audio=bedrock.CfnDataAutomationProject.AudioStandardOutputConfigurationProperty(
                extraction=bedrock.CfnDataAutomationProject.AudioStandardExtractionProperty(
                    category=bedrock.CfnDataAutomationProject.AudioExtractionCategoryProperty(
                        state="ENABLED",
                        type_configuration=bedrock.CfnDataAutomationProject.AudioExtractionCategoryTypeConfigurationProperty(
                            transcript=bedrock.CfnDataAutomationProject.TranscriptConfigurationProperty(
                                channel_labeling=bedrock.CfnDataAutomationProject.ChannelLabelingConfigurationProperty(
                                    state="ENABLED"
                                ),
                                speaker_labeling=bedrock.CfnDataAutomationProject.SpeakerLabelingConfigurationProperty(
                                    state="ENABLED"
                                )
                            )
                        ),
                        types=["TRANSCRIPT"]
                    )
                ),
                generative_field=bedrock.CfnDataAutomationProject.AudioStandardGenerativeFieldProperty(
                    state="ENABLED",
                    types=["AUDIO_SUMMARY", "TOPIC_SUMMARY"]
                )
            ),
            document=bedrock.CfnDataAutomationProject.DocumentStandardOutputConfigurationProperty(
                extraction=bedrock.CfnDataAutomationProject.DocumentStandardExtractionProperty(
                    bounding_box=bedrock.CfnDataAutomationProject.DocumentBoundingBoxProperty(
                        state="DISABLED"
                    ),
                    granularity=bedrock.CfnDataAutomationProject.DocumentExtractionGranularityProperty(
                        types=["PAGE", "DOCUMENT"]
                    )
                ),
                generative_field=bedrock.CfnDataAutomationProject.DocumentStandardGenerativeFieldProperty(
                    state="ENABLED"
                ),
                output_format=bedrock.CfnDataAutomationProject.DocumentOutputFormatProperty(
                    additional_file_format=bedrock.CfnDataAutomationProject.DocumentOutputAdditionalFileFormatProperty(
                        state="ENABLED"
                    ),
                    text_format=bedrock.CfnDataAutomationProject.DocumentOutputTextFormatProperty(
                        types=["MARKDOWN"]
                    )
                )
            ),
            image=bedrock.CfnDataAutomationProject.ImageStandardOutputConfigurationProperty(
                extraction=bedrock.CfnDataAutomationProject.ImageStandardExtractionProperty(
                    bounding_box=bedrock.CfnDataAutomationProject.ImageBoundingBoxProperty(
                        state="DISABLED"
                    ),
                    category=bedrock.CfnDataAutomationProject.ImageExtractionCategoryProperty(
                        state="ENABLED",
                        types=["TEXT_DETECTION"]
                    )
                )
            ),
            video=bedrock.CfnDataAutomationProject.VideoStandardOutputConfigurationProperty(
                extraction=bedrock.CfnDataAutomationProject.VideoStandardExtractionProperty(
                    bounding_box=bedrock.CfnDataAutomationProject.VideoBoundingBoxProperty(
                        state="DISABLED"
                    ),
                    category=bedrock.CfnDataAutomationProject.VideoExtractionCategoryProperty(
                        state="ENABLED",
                        types=["TEXT_DETECTION", "TRANSCRIPT"]
                    )
                ),
                generative_field=bedrock.CfnDataAutomationProject.VideoStandardGenerativeFieldProperty(
                    state="ENABLED",
                    types=["VIDEO_SUMMARY", "CHAPTER_SUMMARY"]
                )
            )
        )

        # Create the project
        project = bedrock.CfnDataAutomationProject(
            self,
            "HealthcareDataAutomationProject",
            project_name=project_name,
            project_description="Healthcare document processing project using multiple medical blueprints",
            custom_output_configuration=bedrock.CfnDataAutomationProject.CustomOutputConfigurationProperty(
                blueprints=blueprint_items
            ),
            standard_output_configuration=standard_output_configuration,

            tags=[
                {
                    "key": "ProjectType",
                    "value": "healthcare"
                },
                {
                    "key": "Environment",
                    "value": "production"
                }
            ]
        )

        return project
