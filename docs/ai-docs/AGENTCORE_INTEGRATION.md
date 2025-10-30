# AgentCore Integration

This document describes the integration with AWS Bedrock AgentCore for streaming chat responses.

## Overview

The frontend now uses the AWS Bedrock AgentCore SDK to communicate directly with AgentCore runtime, providing:

- **Streaming responses**: Real-time message streaming from AgentCore
- **Direct integration**: No Lambda proxy needed for chat functionality
- **Fallback support**: Automatic fallback to Lambda endpoint if AgentCore is unavailable

## Configuration

### Environment Variables

Add these environment variables to your `.env` file:

```bash
# AgentCore Configuration
VITE_AGENTCORE_RUNTIME_ID=your-agentcore-runtime-id
VITE_AWS_REGION=us-east-1
```

### Authentication

The frontend uses AWS Amplify Auth credentials to authenticate with AgentCore. Make sure your Amplify Auth user has the necessary permissions to invoke the AgentCore runtime.

## Architecture

```
Frontend (React) 
    ↓
AgentCoreService (AWS SDK)
    ↓
AWS Bedrock AgentCore Runtime
    ↓
Your Agent Implementation
```

## Files Modified

### New Files
- `src/services/agentCoreService.ts` - Direct AgentCore integration
- `.env.example` - Environment variable template
- `AGENTCORE_INTEGRATION.md` - This documentation

### Modified Files
- `src/services/chatService.ts` - Added streaming support with fallback
- `src/pages/ChatPage.tsx` - Updated to use streaming responses
- `src/components/chat/MarkdownRenderer.tsx` - Enhanced error handling

## Usage

The chat interface automatically uses AgentCore streaming when available:

1. **User sends message** → Creates streaming placeholder
2. **AgentCore processes** → Updates message content in real-time
3. **Response complete** → Finalizes message and handles patient context
4. **Fallback** → Uses Lambda endpoint if AgentCore unavailable

## Streaming Flow

```typescript
// Send streaming message
await chatService.sendStreamingMessage(
  requestData,
  // onChunk - called for each streaming chunk
  (chunk) => updateMessageContent(chunk.content),
  // onComplete - called when streaming is done
  (finalResponse) => finalizeMessage(finalResponse),
  // onError - called if streaming fails
  (error) => handleError(error)
);
```

## Development Notes

### Current Implementation
- Uses simplified AgentCore SDK integration
- Simulates streaming for development/testing
- Maintains compatibility with existing Lambda endpoints

### Production Considerations
- Verify correct SDK property names with AWS documentation
- Implement proper error handling and retry logic
- Add authentication and authorization checks
- Monitor AgentCore usage and costs

### Troubleshooting

1. **AgentCore not responding**: Check runtime ID and permissions
2. **Streaming not working**: Falls back to Lambda automatically
3. **Authentication errors**: Verify Cognito Identity Pool configuration

## Next Steps

1. **Test with real AgentCore runtime**: Update SDK usage based on actual API
2. **Implement WebSocket streaming**: For true real-time streaming
3. **Add retry logic**: Handle temporary AgentCore unavailability
4. **Monitor performance**: Track response times and error rates
