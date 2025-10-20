import {
  Alert,
  Badge,
  Box,
  Button,
  Cards,
  Container,
  FileUpload,
  Header,
  Link,
  ProgressBar,
  SpaceBetween
} from '@cloudscape-design/components';
import type React from 'react';
import { useState } from 'react';
import { storageService } from '../services/storageService';

interface UploadedFile {
  name: string;
  size: number;
  status: 'uploading' | 'success' | 'error';
  key?: string;
  error?: string;
  progress?: number;
}

const DocumentTestPage: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = ({ detail }: { detail: { value: File[] } }) => {
    setFiles(detail.value);
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setIsUploading(true);
    const newUploadedFiles: UploadedFile[] = files.map(file => ({
      name: file.name,
      size: file.size,
      status: 'uploading' as const
    }));

    setUploadedFiles(prev => [...prev, ...newUploadedFiles]);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fileIndex = uploadedFiles.length + i;

      try {
        // Upload to documents/ prefix to trigger the workflow
        const key = `documents/${Date.now()}-${file.name}`;

        await storageService.uploadFile(file, key, {
          contentType: file.type,
          onProgress: (event) => {
            const progress = event.transferredBytes && event.totalBytes
              ? Math.round((event.transferredBytes / event.totalBytes) * 100)
              : 0;

            // Update progress in real-time
            setUploadedFiles(prev => prev.map((f, idx) =>
              idx === fileIndex
                ? { ...f, progress }
                : f
            ));
          }
        });

        // Update status to success
        setUploadedFiles(prev => prev.map((f, idx) =>
          idx === fileIndex
            ? { ...f, status: 'success' as const, key }
            : f
        ));

      } catch (error) {
        console.error(`Failed to upload ${file.name}:`, error);

        // Update status to error
        setUploadedFiles(prev => prev.map((f, idx) =>
          idx === fileIndex
            ? {
              ...f,
              status: 'error' as const,
              error: error instanceof Error ? error.message : 'Upload failed'
            }
            : f
        ));
      }
    }

    setIsUploading(false);
    setFiles([]);
  };

  const clearHistory = () => {
    setUploadedFiles([]);
  };

  return (
    <Container>
      <SpaceBetween size="l">
        <Header
          variant="h1"
          description="Test the document workflow by uploading medical documents"
          actions={
            <Button
              variant="normal"
              onClick={clearHistory}
              disabled={uploadedFiles.length === 0}
            >
              Clear History
            </Button>
          }
        >
          Document Workflow Testing
        </Header>

        <Alert
          type="info"
          header="How it works"
        >
          <SpaceBetween size="s">
            <div>
              Upload medical documents to test the complete workflow:
            </div>
            <ol>
              <li><strong>Upload</strong>: Files are uploaded to the raw S3 bucket</li>
              <li><strong>Processing</strong>: Bedrock Data Automation processes the documents</li>
              <li><strong>Extraction</strong>: Data is extracted and stored in the knowledge base</li>
              <li><strong>Storage</strong>: Processed results are stored in the processed bucket</li>
            </ol>
            <div>
              <strong>Supported formats:</strong> PDF, TXT, DOC, DOCX, images (PNG, JPG)
            </div>
          </SpaceBetween>
        </Alert>

        <SpaceBetween size="m">
          <Header variant="h2">Upload Documents</Header>

          <FileUpload
            onChange={handleFileChange}
            value={files}
            multiple
            accept=".pdf,.txt,.doc,.docx,.png,.jpg,.jpeg"
            showFileLastModified
            showFileSize
            constraintText="Supported formats: PDF, TXT, DOC, DOCX, PNG, JPG. Max 10MB per file."
            i18nStrings={{
              uploadButtonText: e => e ? "Choose files" : "Choose file",
              dropzoneText: e => e ? "Drop files to upload" : "Drop file to upload",
              removeFileAriaLabel: e => `Remove file ${e + 1}`,
              limitShowFewer: "Show fewer files",
              limitShowMore: "Show more files",
              errorIconAriaLabel: "Error"
            }}
          />

          <Button
            variant="primary"
            onClick={uploadFiles}
            disabled={files.length === 0 || isUploading}
            loading={isUploading}
          >
            {isUploading ? 'Uploading...' : `Upload ${files.length} file${files.length !== 1 ? 's' : ''}`}
          </Button>
        </SpaceBetween>

        {uploadedFiles.length > 0 && (
          <SpaceBetween size="m">
            <Header variant="h2">Upload History</Header>

            <Cards
              cardDefinition={{
                header: item => (
                  <SpaceBetween direction="horizontal" size="xs">
                    <Box variant="strong">{item.name}</Box>
                    <Badge
                      color={
                        item.status === 'success' ? 'green' :
                          item.status === 'error' ? 'red' : 'blue'
                      }
                    >
                      {item.status}
                    </Badge>
                  </SpaceBetween>
                ),
                sections: [
                  {
                    id: "details",
                    content: item => (
                      <SpaceBetween size="xs">
                        <div>Size: {(item.size / 1024).toFixed(1)} KB</div>
                        {item.key && <div>Key: {item.key}</div>}

                        {item.status === 'uploading' && (
                          <Box>
                            <SpaceBetween size="xs">
                              <div>Uploading... {item.progress || 0}%</div>
                              <ProgressBar
                                value={item.progress || 0}
                                variant="standalone"
                                label="Upload progress"
                                description={`${item.progress || 0}% complete`}
                              />
                            </SpaceBetween>
                          </Box>
                        )}

                        {item.error && (
                          <Alert type="error">
                            {item.error}
                          </Alert>
                        )}
                        {item.status === 'success' && (
                          <Alert type="success">
                            File uploaded successfully! Check AWS Console for processing status.
                          </Alert>
                        )}
                      </SpaceBetween>
                    )
                  }
                ]
              }}
              items={uploadedFiles}
              loading={isUploading}
              empty={
                <Box textAlign="center" color="inherit">
                  <b>No uploads yet</b>
                  <Box variant="p" color="inherit">
                    Upload some documents to see them here.
                  </Box>
                </Box>
              }
            />
          </SpaceBetween>
        )}

        <Alert
          type="info"
          header="Monitoring the Workflow"
        >
          <SpaceBetween size="s">
            <div>After uploading, monitor the workflow progress in:</div>
            <ul>
              <li>
                <Link external href="https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups">
                  CloudWatch Logs
                </Link> - Check Lambda execution logs
              </li>
              <li>
                <Link external href="https://console.aws.amazon.com/bedrock/home">
                  Bedrock Console
                </Link> - Monitor Data Automation processing
              </li>
              <li>
                <Link external href="https://console.aws.amazon.com/s3/home">
                  S3 Console
                </Link> - View raw and processed files
              </li>
              <li>
                <Link external href="https://console.aws.amazon.com/events/home">
                  EventBridge Console
                </Link> - Check rule executions
              </li>
            </ul>
          </SpaceBetween>
        </Alert>
      </SpaceBetween>
    </Container>
  );
};

export default DocumentTestPage;
