# Chat Components

This directory contains all chat-related components for the medical AI system.

## Components

### Core Chat Components

- **ChatContainer**: Main chat interface wrapper with message history and input area
- **ChatBubble**: Individual message display with avatars and markdown support
- **PromptInput**: Message input with file upload capabilities
- **TypingIndicator**: Loading indicator for AI responses

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

## Requirements Fulfilled

This implementation fulfills the following requirements from the spec:

- **Requirement 6.1**: AI response attachments display with download links
- **Requirement 6.2**: External source citations with clickable links
- **Requirement 6.3**: Multiple attachments organized in clear format
- **Requirement 6.4**: Source metadata display
- **Requirement 6.5**: Proper file viewing/downloading
- **Requirement 4.3**: Patient information integration with chat context
- **Requirement 4.4**: Patient information updates reflected in real-time
- **Requirement 4.5**: Patient context passed to chat

## Future Enhancements

- Real-time file processing status updates via WebSocket
- File preview modal for images and PDFs
- Source preview/summary on hover
- Patient medical history quick view in sidebar
- Recent patient selection history
