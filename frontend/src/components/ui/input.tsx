import { type InputHTMLAttributes, type TextareaHTMLAttributes, forwardRef } from 'react'
import clsx from 'clsx'

const fieldClasses =
  'w-full rounded-xl border border-border bg-surface-raised px-3.5 py-2.5 text-sm text-fg ' +
  'placeholder:text-fg-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent'

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input ref={ref} className={clsx(fieldClasses, className)} {...props} />
  ),
)
Input.displayName = 'Input'

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea ref={ref} className={clsx(fieldClasses, 'resize-none', className)} {...props} />
))
Textarea.displayName = 'Textarea'

export function Label({ children, htmlFor }: { children: string; htmlFor: string }) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-fg-subtle">
      {children}
    </label>
  )
}
