import type { TextareaHTMLAttributes } from 'react'
import styles from './Textarea.module.scss'

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  hasError?: boolean
}

export default function Textarea({
  hasError = false,
  className,
  ...props
}: TextareaProps) {
  const textareaClassName = [
    styles.textarea,
    hasError && styles.error,
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return <textarea className={textareaClassName} {...props} />
}