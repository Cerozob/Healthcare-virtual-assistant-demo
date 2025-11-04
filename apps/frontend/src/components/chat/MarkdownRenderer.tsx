import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './MarkdownRenderer.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

// Helper function to safely render children (handles objects, arrays, etc.)
const renderChildren = (children: React.ReactNode): React.ReactNode => {
  if (typeof children === 'string' || typeof children === 'number' || typeof children === 'boolean') {
    return children;
  }
  if (children === null || children === undefined) {
    return null;
  }
  if (Array.isArray(children)) {
    return children.map((child, index) => {
      // Generate a more stable key using content hash or index as fallback
      const key = typeof child === 'string' ? `${child.slice(0, 20)}-${index}` : `child-${index}`;
      return <span key={key}>{renderChildren(child)}</span>;
    });
  }
  if (typeof children === 'object' && 'props' in children) {
    // It's a React element, render as-is
    return children;
  }
  // For plain objects, stringify them
  try {
    return JSON.stringify(children);
  } catch {
    return String(children);
  }
};

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  // Ensure content is always a string
  const safeContent = typeof content === 'string' ? content : 
                     content === null || content === undefined ? '' :
                     JSON.stringify(content);

  // Debug log for non-string content
  if (typeof content !== 'string') {
    console.warn('MarkdownRenderer received non-string content:', { 
      type: typeof content, 
      content, 
      converted: safeContent 
    });
  }

  return (
    <div className={`markdown-renderer ${className || ''}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}
        components={{
          // Customize heading styles
          h1: ({ children }) => <h1 className="markdown-h1">{renderChildren(children)}</h1>,
          h2: ({ children }) => <h2 className="markdown-h2">{renderChildren(children)}</h2>,
          h3: ({ children }) => <h3 className="markdown-h3">{renderChildren(children)}</h3>,
          h4: ({ children }) => <h4 className="markdown-h4">{renderChildren(children)}</h4>,
          h5: ({ children }) => <h5 className="markdown-h5">{renderChildren(children)}</h5>,
          h6: ({ children }) => <h6 className="markdown-h6">{renderChildren(children)}</h6>,

          // Style paragraphs
          p: ({ children }) => <p className="markdown-p">{renderChildren(children)}</p>,

          // Style code blocks
          code: ({ children, ...props }) => {
            // Check if this is inline code by looking at the node structure
            const isInline = !props.className?.includes('language-');

            if (isInline) {
              return <code className="markdown-code-inline" {...props}>{renderChildren(children)}</code>;
            }
            return (
              <pre className="markdown-code-block">
                <code {...props}>{renderChildren(children)}</code>
              </pre>
            );
          },

          // Style lists
          ul: ({ children }) => <ul className="markdown-ul">{renderChildren(children)}</ul>,
          ol: ({ children }) => <ol className="markdown-ol">{renderChildren(children)}</ol>,
          li: ({ children }) => <li className="markdown-li">{renderChildren(children)}</li>,

          // Style blockquotes
          blockquote: ({ children }) => <blockquote className="markdown-blockquote">{renderChildren(children)}</blockquote>,

          // Style links
          a: ({ children, href, ...props }) => (
            <a className="markdown-link" href={href} {...props}>
              {renderChildren(children)}
            </a>
          ),

          // Style tables
          table: ({ children }) => <table className="markdown-table">{renderChildren(children)}</table>,
          th: ({ children }) => <th className="markdown-th">{renderChildren(children)}</th>,
          td: ({ children }) => <td className="markdown-td">{renderChildren(children)}</td>,

          // Style horizontal rules
          hr: () => <hr className="markdown-hr" />,

          // Style strong/bold text
          strong: ({ children }) => <strong className="markdown-strong">{renderChildren(children)}</strong>,

          // Style emphasis/italic text
          em: ({ children }) => <em className="markdown-em">{renderChildren(children)}</em>
        }}
      >
        {safeContent}
      </ReactMarkdown>
    </div>
  );
}
