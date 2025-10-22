# Chat Components

This directory contains chat-related components for the medical AI system, following AWS Cloudscape Design patterns for generative AI chat interfaces.

## Components

### Core Chat Components

- **ChatContainer**: Main chat interface wrapper with message history, support prompts, and error handling
- **ChatBubble**: Individual message display with avatars, markdown support, and inline feedback actions using Cloudscape components
- **PromptInput**: Message input with file upload capabilities and AI disclaimer
- **ErrorState**: Enhanced error display with retry functionality

### Utility Components

- **AttachmentDisplay**: Displays file attachments from AI responses
- **SourceReferences**: Displays external source citations
- **PatientChatSidebar**: Shows current patient context in chat

## Simplified Architecture

This implementation has been simplified to use Cloudscape components directly where possible, rather than creating unnecessary wrapper components. The `@cloudscape-design/chat-components` package provides the core GenAI components we need.

### Advanced Features (Task 7)

#### AttachmentDisplay
Displays file attachments from AI responses with download and preview functionality.

**Features:**
- File type icons (PDF, images, videos, audio, documents)
- File size formatting
- Processing status indicators (pending, processing, completed, failed)
- Download functionality
- Preview capability for supported file types (images, PDFs, text)

**Usage:**
```tsx
import { AttachmentDisplay } from './components/chat';

<AttachmentDisplay 
  attachments={message.attachments}
  onDownload={(attachment) => console.log('Download', attachment)}
  onPreview={(attachment) => console.log('Preview', attachment)}
/>
```

#### SourceReferences
Displays external source citations with clickable links and metadata.

**Features:**
- Source type categorization (document, website, database)
- Clickable links with external indicators
- Source descriptions and metadata
- Type-specific icons

**Usage:**
```tsx
import { SourceReferences } from './components/chat';

<SourceReferences 
  sources={message.sources}
  onSourceClick={(source) => console.log('Open source', source)}
/>
```

#### PatientChatSidebar
Displays current patient information in the chat interface with switching capability.

**Features:**
- Patient avatar and basic information
- Patient ID and date of birth display
- Change patient button
- Clear patient button
- Active context indicator
- Empty state when no patient selected

**Usage:**
```tsx
import { PatientChatSidebar } from './components/chat';

<PatientChatSidebar
  patient={selectedPatient}
  onChangePatient={() => setShowPatientSelector(true)}
  onClearPatient={() => clearPatient()}
/>
```

## Integration with ChatBubble

The `ChatBubble` component automatically displays attachments and sources when they are present in the message:

```tsx
const message: ChatMessage = {
  id: 'msg_1',
  content: 'Here are the results...',
  type: 'agent',
  timestamp: new Date().toISOString(),
  attachments: [
    {
      id: 'att_1',
      name: 'results.pdf',
      type: 'application/pdf',
      size: 1024000,
      url: 'https://...',
      processingStatus: 'completed'
    }
  ],
  sources: [
    {
      title: 'Medical Guidelines',
      url: 'https://...',
      description: 'Official medical guidelines',
      type: 'document'
    }
  ]
};

<ChatBubble message={message} />
```

## Patient Context Integration

The chat interface now integrates with the PatientContext to:

1. **Display current patient**: Shows patient info in the sidebar
2. **Include patient context in messages**: Automatically adds patient information to chat queries
3. **Allow patient switching**: Modal dialog to select different patients
4. **System messages**: Notifies when patient context changes

### Implementation in ChatPage

```tsx
// Patient context is automatically included in messages
const contextualContent = selectedPatient 
  ? `[Contexto del paciente: ${selectedPatient.full_name} (ID: ${selectedPatient.patient_id})]\n\n${content}`
  : content;

// Patient sidebar shows current patient
<PatientChatSidebar
  patient={selectedPatient}
  onChangePatient={handleChangePatient}
  onClearPatient={handleClearPatient}
/>

// Modal for patient selection
<Modal visible={showPatientSelector}>
  <PatientSelector 
    onPatientSelect={handlePatientSelect}
    onPatientSelected={handlePatientSelected}
  />
</Modal>
```

## Type Definitions

All types are exported from the components and also available in `types/api.ts`:

```typescript
interface FileAttachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  processingStatus?: 'pending' | 'processing' | 'completed' | 'failed';
}

interface ExternalSource {
  title: string;
  url: string;
  description?: string;
  type: 'document' | 'website' | 'database';
}

interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'agent' | 'system';
  agentType?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
  attachments?: FileAttachment[];
  sources?: ExternalSource[];
}
```

## Cloudscape Design Compliance

This implementation follows AWS Cloudscape Design patterns for generative AI chat:

### ✅ Implemented Features:
- **AI Output Labels**: "Generated by AI" labels with sparkle icons on all AI responses
- **Proper GenAI Loading States**: Two-stage loading (processing → generating) with avatar loading indicators
- **Enhanced Typing Indicators**: Contextual loading messages ("Processing your request" → "Generating a response")
- **GenAI Terminology**: Uses "generative AI assistant", "submit" for user actions, "responses" for AI replies
- **Avatars**: Distinct visual representation for user vs AI messages with loading states
- **Feedback System**: Thumbs up/down with detailed feedback collection using proper GenAI terminology
- **Inline Actions**: Copy to clipboard, feedback buttons always visible
- **Support Prompts**: Contextual suggested prompts based on conversation state
- **Error States**: Enhanced error handling with retry functionality
- **Source Citations**: Clickable external source references
- **File Attachments**: Comprehensive file upload and display
- **AI Disclaimer**: Constraint text warning about generative AI limitations
- **Stacked Bubbles**: Support for complex content in separate bubbles
- **Streaming Support**: Components ready for streaming responses with proper loading indicators

### 🎯 Key Improvements Made:
1. **GenAI Output Labels**: Added "Generated by AI" labels with sparkle icons to all AI responses
2. **Two-Stage Loading**: Implemented processing → generating loading stages with proper messaging
3. **Enhanced Avatar Loading**: Avatar shows loading spinner during AI processing/generation
4. **Proper GenAI Terminology**: Updated all text to use Cloudscape-approved GenAI terminology
5. **Enhanced Feedback Flow**: Complete thumbs up/down system with GenAI-specific feedback collection
6. **Contextual Support Prompts**: Dynamic prompt suggestions based on conversation state and patient context
7. **Better Error Handling**: Categorized errors with appropriate retry mechanisms
8. **Inline Actions**: Always-visible action buttons for AI responses
9. **GenAI Disclaimer**: Added constraint text about generative AI limitations using proper terminology
10. **Streaming Components**: Created components ready for streaming responses with loading bars

## Requirements Fulfilled

This implementation fulfills the following requirements:

- **Requirement 6.1**: AI response attachments display with download links
- **Requirement 6.2**: External source citations with clickable links
- **Requirement 6.3**: Multiple attachments organized in clear format
- **Requirement 6.4**: Source metadata display
- **Requirement 6.5**: Proper file viewing/downloading
- **Requirement 4.3**: Patient information integration with chat context
- **Requirement 4.4**: Patient information updates reflected in real-time
- **Requirement 4.5**: Patient context passed to chat
- **Cloudscape Compliance**: Follows AWS Cloudscape Design patterns for generative AI chat

## Usage Examples

### Basic Chat Implementation
```tsx
import { ChatContainer, ChatBubble, PromptInput } from './components/chat';

// In your chat page
<ChatContainer
  messages={messages}
  onSendMessage={handleSendMessage}
  isLoading={isLoading}
  error={error}
  hasPatientContext={hasPatient}
>
  {messages.map((message) => (
    <ChatBubble 
      key={message.id} 
      message={message} 
      onFeedback={handleFeedback}
    />
  ))}
</ChatContainer>

<PromptInput
  onSendMessage={handleSendMessage}
  isLoading={isLoading}
/>
```

### Using Cloudscape GenAI Components Directly
For more advanced use cases, you can import and use Cloudscape GenAI components directly:

```tsx
import { ChatBubble, Avatar, LoadingBar } from '@cloudscape-design/chat-components';

// Custom loading indicator
<ChatBubble
  avatar={<Avatar initials="AI" color="green" loading />}
  content=""
  additionalContent={<LoadingBar status="in-progress" label="Generating response" />}
/>
```

## Future Enhancements

- Real-time streaming integration with WebSocket
- Progressive loading for complex AI-generated content
- Enhanced accessibility for screen readers
- Real-time file processing status updates via WebSocket
- File preview modal for images and PDFs
- Source preview/summary on hover
- Patient medical history quick view in sidebar
- Recent patient selection history
