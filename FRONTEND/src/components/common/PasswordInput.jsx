import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'

export function PasswordInput({ className = '', ...props }) {
  const [visible, setVisible] = useState(false)
  const inputClassName = ['password-input__field', className].filter(Boolean).join(' ')

  return (
    <span className="password-input">
      <input {...props} className={inputClassName} type={visible ? 'text' : 'password'} />
      <button
        type="button"
        className="password-input__toggle"
        aria-label={visible ? 'Hide password' : 'Show password'}
        aria-pressed={visible}
        onClick={() => setVisible((current) => !current)}
      >
        {visible ? <EyeSlashIcon aria-hidden="true" /> : <EyeIcon aria-hidden="true" />}
      </button>
    </span>
  )
}