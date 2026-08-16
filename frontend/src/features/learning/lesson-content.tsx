import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function LessonContent({ markdown }: { markdown: string }) {
  return (
    <div
      className={[
        'prose prose-invert prose-sm max-w-none',
        'prose-headings:text-heading prose-headings:font-semibold',
        'prose-p:text-fg prose-li:text-fg prose-strong:text-fg',
        'prose-a:text-accent-light prose-a:no-underline hover:prose-a:underline',
        'prose-code:text-accent-light prose-code:before:content-none prose-code:after:content-none',
        'prose-pre:bg-surface-raised prose-pre:border prose-pre:border-border',
        'prose-blockquote:text-fg-muted prose-blockquote:border-accent',
        'prose-th:text-heading prose-td:text-fg-muted',
        'prose-hr:border-border',
      ].join(' ')}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
    </div>
  )
}
