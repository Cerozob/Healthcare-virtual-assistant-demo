// TODO: Align these types with backend Lambda response schemas

export interface ChatMessage {
  id: string;
  content: string;
  type: "user" | "agent";
  timestamp: string;
  agentType?: "orchestrator" | "information_retrieval" | "scheduling";
  attachments?: ChatAttachment[];
  metadata?: Record<string, any>;
}

export interface ChatAttachment {
  name: string;
  size: number;
  type: string;
  url?: string;
  s3Key?: string;
  status?: "uploading" | "processing" | "complete" | "error";
}

export interface ChatSession {
  id: string;
  userId?: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
  context?: Record<string, any>;
  status: "active" | "archived";
}

// TODO: Add WebSocket message types for real-time communication
export interface WebSocketMessage {
  type: "message" | "typing" | "status" | "error";
  payload: any;
}
