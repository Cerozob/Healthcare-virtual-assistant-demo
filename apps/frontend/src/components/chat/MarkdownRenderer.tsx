import ReactMarkdown from 'react-markdown';
import './MarkdownRenderer.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={`markdown-renderer ${className || ''}`}>
      <ReactMarkdown
        components={{
          // Customize heading styles
          h1: ({ children }) => <h1 className="markdown-h1">{children}</h1>,
          h2: ({ children }) => <h2 className="markdown-h2">{children}</h2>,
          h3: ({ children }) => <h3 className="markdown-h3">{children}</h3>,
          h4: ({ children }) => <h4 className="markdown-h4">{children}</h4>,
          h5: ({ children }) => <h5 className="markdown-h5">{children}</h5>,
          h6: ({ children }) => <h6 className="markdown-h6">{children}</h6>,

          // Style paragraphs
          p: ({ children }) => <p className="markdown-p">{children}</p>,

          // Style code blocks
          code: ({ children, ...props }) => {
            // Check if this is inline code by looking at the node structure
            const isInline = !props.className?.includes('language-');

            if (isInline) {
              return <code className="markdown-code-inline" {...props}>{children}</code>;
            }
            return (
              <pre className="markdown-code-block">
                <code {...props}>{children}</code>
              </pre>
            );
          },

          // Style lists
          ul: ({ children }) => <ul className="markdown-ul">{children}</ul>,
          ol: ({ children }) => <ol className="markdown-ol">{children}</ol>,
          li: ({ children }) => <li className="markdown-li">{children}</li>,

          // Style blockquotes
          blockquote: ({ children }) => <blockquote className="markdown-blockquote">{children}</blockquote>,

          // Style links
          a: ({ children, href, ...props }) => (
            <a className="markdown-link" href={href} {...props}>
              {children}
            </a>
          ),

          // Style tables
          table: ({ children }) => <table className="markdown-table">{children}</table>,
          th: ({ children }) => <th className="markdown-th">{children}</th>,
          td: ({ children }) => <td className="markdown-td">{children}</td>,

          // Style horizontal rules
          hr: () => <hr className="markdown-hr" />,

          // Style strong/bold text
          strong: ({ children }) => <strong className="markdown-strong">{children}</strong>,

          // Style emphasis/italic text
          em: ({ children }) => <em className="markdown-em">{children}</em>
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
