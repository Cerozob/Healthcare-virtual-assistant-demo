# Max Tokens Error Handling

## Overview

The sample generator now includes robust error handling for AWS Bedrock max_tokens quota limitations. When the model hits token limits, the system will automatically retry with exponential backoff and provide fallback mechanisms.

## Error Handling Features

### 1. Automatic Retry with Exponential Backoff

- **Max Retries**: 3 attempts by default
- **Base Delay**: 1-2 seconds, doubles with each retry
- **Jitter**: Random 0-1 second added to prevent thundering herd
- **Error Detection**: Automatically detects max_tokens related errors

### 2. Fallback Mechanisms

When batch generation fails:
1. **Individual Document Generation**: Tries generating documents one by one
2. **Simplified Prompts**: Uses shorter, more concise prompts
3. **Graceful Degradation**: Provides minimal content when generation fails
4. **Process Continuation**: Continues with next patient instead of failing completely

### 3. Improved Resilience

- **Consecutive Failure Handling**: Adds longer delays after multiple failures
- **Progress Preservation**: Saves intermediate results to prevent data loss
- **Detailed Logging**: Comprehensive error logging for debugging

## Configuration Options

### Reducing Token Usage

To reduce the likelihood of max_tokens errors, you can:

1. **Lower max_tokens in config.json**:
   ```json
   {
     "bedrock": {
       "max_tokens": 3072
     }
   }
   ```

2. **Generate fewer document types**:
   ```json
   {
     "generation": {
       "document_types": [
         "historia_clinica"
       ]
     }
   }
   ```

3. **Use simpler profiles**: The system now uses more concise prompts automatically

### Retry Configuration

You can adjust retry behavior in the code:

```python
# In bedrock_agent.py
narratives = self._retry_with_backoff(
    _generate_narratives,
    max_retries=5,      # Increase retries
    base_delay=3.0      # Longer initial delay
)
```

## Monitoring and Troubleshooting

### Log Messages to Watch For

- `Max tokens error on attempt X/Y. Retrying in X.XX seconds`
- `Max retries exhausted for max_tokens error`
- `Attempting fallback: generating documents individually`
- `Using fallback narratives to continue processing`

### Common Scenarios

1. **Temporary Quota Issues**: System will retry automatically
2. **Persistent Quota Issues**: System will use fallback generation
3. **Complete Service Issues**: System will provide minimal content and continue

### Recovery Options

If generation fails completely:

1. **Use Recovery Mode**:
   ```bash
   python medical_records_generator.py --recover-only
   ```

2. **Reduce Batch Size**:
   ```bash
   python medical_records_generator.py --count 1
   ```

3. **Check AWS Quotas**: Verify your Bedrock service quotas in AWS Console

## Best Practices

1. **Monitor Logs**: Watch for patterns in max_tokens errors
2. **Adjust Configuration**: Lower max_tokens if errors are frequent
3. **Use Recovery Mode**: Regularly check for incomplete patients
4. **Batch Processing**: Generate smaller batches during high-usage periods
5. **Time of Day**: Consider running during off-peak hours

## Error Types Handled

The system automatically handles these error patterns:

### Max Tokens Errors (with retry):
- `max_tokens`
- `token limit`
- `context length`
- `stop_reason: max_tokens`
- `unrecoverable state`
- `Model returned stop_reason: max_tokens instead of "tool_use"`

### Pydantic Validation Errors (with fallback):
- `validation error` with `input should be a valid list`
- `field required` validation errors
- Incomplete structured output from the model

### Handling Strategy:
1. **Max Tokens Errors**: Automatic retry with exponential backoff
2. **Validation Errors**: Immediate fallback to simplified generation
3. **Other Errors**: Logged and re-raised for investigation

## Implementation Details

### Retry Logic Flow

1. **Initial Attempt**: Try batch generation
2. **Error Detection**: Check if error is max_tokens related
3. **Exponential Backoff**: Wait with increasing delays
4. **Fallback**: Switch to individual generation if batch fails
5. **Graceful Degradation**: Provide minimal content if all fails
6. **Continue Processing**: Move to next patient

### Prompt Optimization

The system now uses:
- **Shorter prompts** for reduced token usage
- **Essential information only** in prompts
- **Structured data** instead of verbose descriptions
- **Fallback content** when generation fails

This ensures the system remains functional even under AWS quota constraints while maintaining data quality and processing continuity.
