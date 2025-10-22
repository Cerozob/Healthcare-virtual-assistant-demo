# Markdown Support in Chat Messages

The chat interface now supports full markdown rendering for AI responses, making it easy to display formatted content, code examples, tables, and more.

## Features

### Text Formatting
- **Bold text** using `**bold**` or `__bold__`
- *Italic text* using `*italic*` or `_italic_`
- `Inline code` using backticks
- ~~Strikethrough~~ using `~~text~~`

### Headings
```markdown
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6
```

### Lists
```markdown
- Unordered list item 1
- Unordered list item 2
  - Nested item
  - Another nested item

1. Ordered list item 1
2. Ordered list item 2
   1. Nested ordered item
   2. Another nested ordered item
```

### Code Blocks
````markdown
```javascript
function example() {
  console.log("Hello, World!");
  return "Markdown works!";
}
```
````

### Tables
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1    | Data     | More data|
| Row 2    | Data     | More data|
```

### Links
```markdown
[Link text](https://example.com)
[AWS Documentation](https://docs.aws.amazon.com)
```

### Blockquotes
```markdown
> This is a blockquote
> It can span multiple lines
> 
> And include multiple paragraphs
```

### Horizontal Rules
```markdown
---
```

## Implementation

The markdown rendering is handled by the `MarkdownRenderer` component, which uses `react-markdown` with custom styling that matches the Cloudscape Design System.

### Usage in Components
```tsx
import { MarkdownRenderer } from '../components/chat';

// In your component
<MarkdownRenderer content={message.content} />
```

### Styling
The component includes custom CSS classes that follow Cloudscape design tokens:
- Typography matches Cloudscape font sizes and weights
- Colors use Cloudscape color palette
- Spacing follows Cloudscape spacing scale
- Responsive design for mobile devices

## Example Response

When you send a message to the chat, the AI assistant will respond with formatted markdown content that demonstrates various markdown features including:

- Headings and subheadings
- Bold and italic text
- Code blocks with syntax highlighting
- Tables with proper formatting
- Lists and nested lists
- Blockquotes for important information
- Links to external resources

## Browser Compatibility

The markdown renderer works in all modern browsers and is fully responsive for mobile devices.

## Accessibility

The rendered markdown maintains proper semantic HTML structure for screen readers and other assistive technologies.
