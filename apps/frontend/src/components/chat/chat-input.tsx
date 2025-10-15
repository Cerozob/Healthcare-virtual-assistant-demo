import { useState, useRef } from "react";
import {
  Box,
  Button,
  FormField,
  Textarea,
  SpaceBetween,
  Icon,
} from "@cloudscape-design/components";

interface ChatInputProps {
  onSendMessage: (content: string, files?: File[]) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (message.trim() || files.length > 0) {
      onSendMessage(message, files);
      setMessage("");
      setFiles([]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      // TODO: Validate file types (PDF, images, medical documents)
      // TODO: Validate file size limits
      // TODO: Show file preview
      setFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <Box>
      <SpaceBetween size="s">
        {/* TODO: Implement file upload preview with thumbnails */}
        {files.length > 0 && (
          <Box>
            <SpaceBetween size="xs">
              {files.map((file, idx) => (
                <Box key={idx}>
                  <SpaceBetween size="xxs" direction="horizontal">
                    <Icon name="file" />
                    <span>{file.name}</span>
                    <Button
                      variant="icon"
                      iconName="close"
                      onClick={() => removeFile(idx)}
                    />
                  </SpaceBetween>
                </Box>
              ))}
            </SpaceBetween>
          </Box>
        )}

        <FormField>
          <Textarea
            value={message}
            onChange={({ detail }) => setMessage(detail.value)}
            onKeyDown={(event) => handleKeyPress(event.detail as any)}
            placeholder="Escribe tu mensaje... (Shift+Enter para nueva línea)"
            rows={3}
            disabled={disabled}
          />
        </FormField>

        <Box float="right">
          <SpaceBetween size="xs" direction="horizontal">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
              style={{ display: "none" }}
              onChange={handleFileSelect}
            />
            <Button
              iconName="upload"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
            >
              Adjuntar Archivos
            </Button>
            <Button
              variant="primary"
              iconName="external"
              onClick={handleSend}
              disabled={disabled || (!message.trim() && files.length === 0)}
            >
              Enviar
            </Button>
          </SpaceBetween>
        </Box>
      </SpaceBetween>
    </Box>
  );
}
