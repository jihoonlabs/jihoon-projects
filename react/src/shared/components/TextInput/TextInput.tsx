import type { InputHTMLAttributes } from 'react'
import styles from './TextInput.module.scss'

type TextInputProps = InputHTMLAttributes<HTMLInputElement> & {
  hasError?: boolean
}

export default function TextInput({
  hasError = false,
  className,
  type = 'text',
  ...props
}: TextInputProps) {
  const inputClassName = [
    styles.input,
    hasError && styles.error,
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <input
      type={type}
      className={inputClassName}
      aria-invalid={hasError}
      {...props}
    />
  )
}