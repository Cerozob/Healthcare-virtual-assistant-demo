-- Chat Sessions Table
-- Stores chat session metadata and context

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),  -- TODO: Link to user authentication system
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    context JSONB DEFAULT '{}',  -- Store session context (patient info, preferences, etc.)
    metadata JSONB DEFAULT '{}'  -- Additional metadata
);

-- Chat Messages Table
-- Stores individual messages in conversations

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL CHECK (message_type IN ('user', 'agent')),
    agent_type VARCHAR(50) CHECK (agent_type IN ('orchestrator', 'information_retrieval', 'scheduling')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'  -- Store agent-specific metadata, citations, etc.
);

-- Chat Attachments Table
-- Stores file attachments associated with messages

CREATE TABLE IF NOT EXISTS chat_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    s3_key VARCHAR(500) NOT NULL,  -- S3 object key
    s3_bucket VARCHAR(255) NOT NULL,
    upload_status VARCHAR(50) DEFAULT 'uploading' CHECK (upload_status IN ('uploading', 'processing', 'complete', 'error')),
    processing_status JSONB DEFAULT '{}',  -- Document processing status from workflow
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp DESC);
CREATE INDEX idx_chat_messages_type ON chat_messages(message_type);

CREATE INDEX idx_chat_attachments_message_id ON chat_attachments(message_id);
CREATE INDEX idx_chat_attachments_s3_key ON chat_attachments(s3_key);
CREATE INDEX idx_chat_attachments_status ON chat_attachments(upload_status);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_attachments_updated_at BEFORE UPDATE ON chat_attachments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- TODO: Add indexes for JSONB fields if needed for specific queries
-- TODO: Consider partitioning for large-scale deployments
-- TODO: Add retention policy for archived sessions
