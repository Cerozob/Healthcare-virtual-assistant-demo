"""
Unit tests for model type detection utilities.

Tests cover:
- Foundation model ID detection
- Inference profile ID detection
- Edge cases and invalid model identifier formats
- Region validation for inference profiles
- ARN pattern generation
- Permission generation
"""

import pytest
from infrastructure.constructs.ai.model_utils import (
    detect_model_type,
    get_model_arn_pattern,
    get_model_permissions,
    get_model_resource_arns,
    create_model_configuration,
    validate_model_identifier,
    ModelType,
    ModelConfiguration,
    InvalidModelIdentifierError,
    BedrockModelError,
    InferenceProfilePermissionError,
)


class TestDetectModelType:
    """Test cases for detect_model_type function."""

    def test_foundation_model_detection(self):
        """Test that foundation model IDs are correctly identified."""
        test_cases = [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "amazon.titan-text-express-v1",
            "cohere.command-text-v14",
            "ai21.j2-ultra-v1",
            "meta.llama2-13b-chat-v1",
        ]

        for model_id in test_cases:
            identifier, is_inference_profile = detect_model_type(model_id)
            assert identifier == model_id
            assert (
                not is_inference_profile
            ), f"Expected foundation model, got inference profile for {model_id}"

    def test_inference_profile_detection(self):
        """Test that inference profile IDs are correctly identified."""
        test_cases = [
            "us.anthropic.claude-3-sonnet-20240229-v1:0",
            "eu.amazon.titan-text-express-v1",
            "ap.cohere.command-text-v14",
            "ca.ai21.j2-ultra-v1",
            "us.meta.llama2-13b-chat-v1",
        ]

        for model_id in test_cases:
            identifier, is_inference_profile = detect_model_type(model_id)
            assert identifier == model_id
            assert (
                is_inference_profile
            ), f"Expected inference profile, got foundation model for {model_id}"

    def test_invalid_model_identifiers(self):
        """Test that invalid model identifiers raise appropriate errors."""
        invalid_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "invalid",  # No dots
            "invalid.format",  # Missing version
            "too.many.dots.in.foundation.model",  # Too many dots for foundation model
            "xy.anthropic.claude-3-sonnet-20240229-v1:0",  # Invalid region prefix
            "123.anthropic.claude-3-sonnet-20240229-v1:0",  # Numeric region prefix
        ]

        for invalid_id in invalid_cases:
            with pytest.raises(InvalidModelIdentifierError):
                detect_model_type(invalid_id)

    def test_none_and_non_string_inputs(self):
        """Test that None and non-string inputs raise appropriate errors."""
        invalid_inputs = [None, 123, [], {}, True]

        for invalid_input in invalid_inputs:
            with pytest.raises(InvalidModelIdentifierError):
                detect_model_type(invalid_input)

    def test_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        test_cases = [
            f"  {model_id}  ",  # Leading and trailing spaces
            f"\t{model_id}\t",  # Leading and trailing tabs
            f"\n{model_id}\n",  # Leading and trailing newlines
        ]

        for test_case in test_cases:
            identifier, is_inference_profile = detect_model_type(test_case)
            assert identifier == model_id
            assert not is_inference_profile


class TestRegionValidation:
    """Test cases for region prefix validation."""

    def test_valid_region_prefixes(self):
        """Test that valid region prefixes are accepted."""
        valid_regions = ["us", "eu", "ap", "ca", "sa", "af", "me"]

        for region in valid_regions:
            model_id = f"{region}.anthropic.claude-3-sonnet-20240229-v1:0"
            identifier, is_inference_profile = detect_model_type(model_id)
            assert identifier == model_id
            assert is_inference_profile

    def test_invalid_region_prefixes(self):
        """Test that invalid region prefixes are rejected."""
        invalid_regions = ["xy", "zz", "123", "invalid"]

        for region in invalid_regions:
            model_id = f"{region}.anthropic.claude-3-sonnet-20240229-v1:0"
            with pytest.raises(InvalidModelIdentifierError):
                detect_model_type(model_id)


class TestArnPatternGeneration:
    """Test cases for ARN pattern generation."""

    def test_foundation_model_arn_pattern(self):
        """Test ARN pattern generation for foundation models."""
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        arn_pattern = get_model_arn_pattern(model_id, False)
        assert arn_pattern == "arn:aws:bedrock:*::foundation-model/*"

    def test_inference_profile_arn_pattern(self):
        """Test ARN pattern generation for inference profiles."""
        model_id = "us.anthropic.claude-3-sonnet-20240229-v1:0"
        arn_pattern = get_model_arn_pattern(model_id, True)
        assert arn_pattern == "arn:aws:bedrock:*:*:inference-profile/*"


class TestPermissionGeneration:
    """Test cases for permission generation."""

    def test_foundation_model_permissions(self):
        """Test permission generation for foundation models."""
        permissions = get_model_permissions(False)
        expected_permissions = [
            "bedrock:InvokeModel",
            "bedrock:InvokeModelWithResponseStream",
        ]
        assert permissions == expected_permissions

    def test_inference_profile_permissions(self):
        """Test permission generation for inference profiles."""
        permissions = get_model_permissions(True)
        expected_permissions = [
            "bedrock:InvokeModel",
            "bedrock:InvokeModelWithResponseStream",
            "bedrock:GetInferenceProfile",
            "bedrock:ListInferenceProfiles",
        ]
        assert permissions == expected_permissions


class TestResourceArnGeneration:
    """Test cases for resource ARN generation."""

    def test_foundation_model_resource_arns(self):
        """Test resource ARN generation for foundation models."""
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        resource_arns = get_model_resource_arns(model_id, False)
        expected_arns = [f"arn:aws:bedrock:*::foundation-model/{model_id}"]
        assert resource_arns == expected_arns

    def test_inference_profile_resource_arns(self):
        """Test resource ARN generation for inference profiles."""
        model_id = "us.anthropic.claude-3-sonnet-20240229-v1:0"
        resource_arns = get_model_resource_arns(model_id, True)
        expected_arns = [
            "arn:aws:bedrock:*::foundation-model/*",
            "arn:aws:bedrock:*:*:inference-profile/*",
            "arn:aws:bedrock:*:*:application-inference-profile/*",
        ]
        assert resource_arns == expected_arns


class TestModelConfiguration:
    """Test cases for model configuration creation."""

    def test_foundation_model_configuration(self):
        """Test model configuration creation for foundation models."""
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        config = create_model_configuration(model_id)

        assert isinstance(config, ModelConfiguration)
        assert config.identifier == model_id
        assert config.model_type == ModelType.FOUNDATION_MODEL
        assert config.arn_pattern == "arn:aws:bedrock:*::foundation-model/*"
        assert "bedrock:InvokeModel" in config.permissions
        assert "bedrock:GetInferenceProfile" not in config.permissions

    def test_inference_profile_configuration(self):
        """Test model configuration creation for inference profiles."""
        model_id = "us.anthropic.claude-3-sonnet-20240229-v1:0"
        config = create_model_configuration(model_id)

        assert isinstance(config, ModelConfiguration)
        assert config.identifier == model_id
        assert config.model_type == ModelType.INFERENCE_PROFILE
        assert config.arn_pattern == "arn:aws:bedrock:*:*:inference-profile/*"
        assert "bedrock:InvokeModel" in config.permissions
        assert "bedrock:GetInferenceProfile" in config.permissions
        assert "bedrock:ListInferenceProfiles" in config.permissions

    def test_invalid_configuration(self):
        """Test that invalid model identifiers raise errors during configuration."""
        with pytest.raises(InvalidModelIdentifierError):
            create_model_configuration("invalid.model.identifier")


class TestValidateModelIdentifier:
    """Test cases for model identifier validation."""

    def test_valid_identifiers(self):
        """Test that valid identifiers return True."""
        valid_identifiers = [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "us.anthropic.claude-3-sonnet-20240229-v1:0",
            "amazon.titan-text-express-v1",
            "eu.cohere.command-text-v14",
        ]

        for identifier in valid_identifiers:
            assert validate_model_identifier(identifier) is True

    def test_invalid_identifiers(self):
        """Test that invalid identifiers return False."""
        invalid_identifiers = [
            "",
            "invalid",
            "too.many.dots.in.foundation.model",
            "xy.anthropic.claude-3-sonnet-20240229-v1:0",
            None,
        ]

        for identifier in invalid_identifiers:
            assert validate_model_identifier(identifier) is False


class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_case_sensitivity(self):
        """Test that model identifiers are case-sensitive."""
        # Foundation model with uppercase should be invalid
        with pytest.raises(InvalidModelIdentifierError):
            detect_model_type("ANTHROPIC.CLAUDE-3-SONNET-20240229-V1:0")

        # Inference profile with uppercase region should be invalid
        with pytest.raises(InvalidModelIdentifierError):
            detect_model_type("US.anthropic.claude-3-sonnet-20240229-v1:0")

    def test_special_characters_in_model_names(self):
        """Test handling of special characters in model names."""
        valid_cases = [
            "anthropic.claude-3-sonnet-20240229-v1:0",  # Hyphens and colons
            "us.amazon.titan-embed-text-v1",  # Hyphens
            "eu.ai21.j2-ultra-v1",  # Numbers and hyphens
        ]

        for case in valid_cases:
            identifier, _ = detect_model_type(case)
            assert identifier == case

    def test_minimum_valid_formats(self):
        """Test minimum valid formats for each model type."""
        # Minimum foundation model format
        min_foundation = "a.b-v1"
        identifier, is_inference_profile = detect_model_type(min_foundation)
        assert identifier == min_foundation
        assert not is_inference_profile

        # Minimum inference profile format
        min_inference = "us.a.b-v1"
        identifier, is_inference_profile = detect_model_type(min_inference)
        assert identifier == min_inference
        assert is_inference_profile


if __name__ == "__main__":
    pytest.main([__file__])
