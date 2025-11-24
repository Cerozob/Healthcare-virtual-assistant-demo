# Sample Generator Usage Guide - Max Tokens Error Handling

## Quick Start

The sample generator now includes robust error handling for AWS Bedrock max_tokens quota limitations. Here's how to use it effectively:

### Basic Usage

```bash
# Generate 5 patients with error handling
python medical_records_generator.py --count 5

# Use low-token configuration to reduce errors
python medical_records_generator.py --count 5 --config config_low_tokens.json

# Recover any incomplete patients
python medical_records_generator.py --recover-only
```

### Error Handling Features

1. **Automatic Retry**: System retries up to 3 times with exponential backoff
2. **Fallback Generation**: If batch fails, tries individual document generation
3. **Graceful Degradation**: Provides minimal content when generation fails
4. **Process Continuation**: Continues with next patient instead of stopping

### Monitoring Progress

Watch the logs for these key messages:

```
✅ Success: "Successfully generated narratives for 3 document types"
⚠️  Retry: "Max tokens error on attempt 1/3. Retrying in 2.34 seconds"
🔄 Fallback: "Attempting fallback: generating documents individually"
⏭️  Continue: "Using fallback narratives to continue processing"
```

### Configuration Options

#### Reduce Token Usage (Recommended)

Use the provided low-token configuration:
```bash
python medical_records_generator.py --config config_low_tokens.json
```

Or create your own with reduced max_tokens:
```json
{
  "bedrock": {
    "max_tokens": 2048
  }
}
```

#### Generate Fewer Documents

Reduce document types to minimize token usage:
```json
{
  "generation": {
    "document_types": [
      "historia_clinica"
    ]
  }
}
```

### Troubleshooting

#### Frequent Max Tokens Errors

1. **Use Lower Token Limit**:
   ```bash
   python medical_records_generator.py --config config_low_tokens.json
   ```

2. **Generate Smaller Batches**:
   ```bash
   python medical_records_generator.py --count 1
   ```

3. **Check AWS Quotas**: Verify Bedrock quotas in AWS Console

#### Recovery from Failures

1. **Check for Incomplete Patients**:
   ```bash
   python medical_records_generator.py --recover-only
   ```

2. **Resume Generation**:
   ```bash
   # The system automatically skips completed patients
   python medical_records_generator.py --count 10
   ```

#### Complete Service Outage

If Bedrock is completely unavailable:
1. System will provide minimal fallback content
2. Check `generation_summary.json` for completion status
3. Use recovery mode when service is restored

### Testing Error Handling

Test the error handling system:
```bash
# Test max_tokens retry logic
python test_error_handling.py

# Test Pydantic validation handling
python test_pydantic_validation.py
```

This will verify:
- Retry logic works correctly for max_tokens errors
- Pydantic validation errors are handled properly
- Fallback mechanisms activate when needed
- System continues processing after errors

### Best Practices

1. **Start Small**: Begin with `--count 1` to test your setup
2. **Monitor Logs**: Watch for error patterns and adjust configuration
3. **Use Recovery**: Regularly run `--recover-only` to complete partial work
4. **Off-Peak Hours**: Run large batches during low AWS usage periods
5. **Backup Configuration**: Keep both normal and low-token configs available

### Error Types Handled

The system automatically handles:
- `Model returned stop_reason: max_tokens instead of "tool_use"`
- `Agent has reached an unrecoverable state due to max_tokens limit`
- `max_tokens`, `token limit`, `context length` errors
- Network timeouts and temporary service issues

### Output Structure

Even with errors, the system maintains consistent output:

```
output/
├── patient_123/
│   ├── patient_123_profile.json
│   ├── patient_123_historia_clinica_*.pdf
│   └── patient_123_receta_medica_*.pdf
├── .intermediate/  # Temporary files for recovery
└── generation_summary.json
```

### Performance Tips

1. **Batch Size**: Use smaller batches (1-5 patients) during high-error periods
2. **Time of Day**: AWS quotas reset periodically, try different times
3. **Model Selection**: Consider using smaller models if available
4. **Document Types**: Generate only essential document types initially

### Support

If you continue experiencing issues:

1. Check the detailed logs in `generator.log`
2. Review AWS Bedrock service health
3. Verify your AWS credentials and permissions
4. Consider increasing your Bedrock service quotas

The system is designed to be resilient and continue processing even under quota constraints while maintaining data quality.
