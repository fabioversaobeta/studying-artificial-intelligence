import ReactMarkdown from 'react-markdown'

/** Renders short markdown (inline code, emphasis) without block wrappers, for option labels. */
export function InlineMarkdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      components={{
        p: ({ children: content }) => <span>{content}</span>,
        code: ({ children: content }) => (
          <code className="rounded bg-surface-raised px-1 py-0.5 text-[0.85em] text-accent-light">
            {content}
          </code>
        ),
      }}
    >
      {children}
    </ReactMarkdown>
  )
}
