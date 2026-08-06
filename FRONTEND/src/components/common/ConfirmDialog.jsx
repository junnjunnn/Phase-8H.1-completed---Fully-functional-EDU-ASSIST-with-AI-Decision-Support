import { useEffect, useRef } from 'react'
function InlineIcon({ children, className = 'icon' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {children}
    </svg>
  )
}

export function ConfirmDialog({ open, title, message, confirmLabel = 'Confirm', cancelLabel = 'Cancel', onConfirm, onCancel }) {
  const dialogRef = useRef(null)

  useEffect(() => {
    if (!open) return

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onCancel?.()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onCancel])

  if (!open) return null

  return (
    <div className="modal-backdrop" role="presentation" onClick={onCancel}>
      <div className="modal-card modal-card--compact" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title" ref={dialogRef} onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-wrap"><InlineIcon><path d="M12 9v4" /><path d="M12 17h.01" /><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" /></InlineIcon></div>
            <div>
              <p className="eyebrow">Confirmation</p>
              <h3 id="confirm-dialog-title">{title}</h3>
            </div>
          </div>
        </div>
        <p className="modal-description">{message}</p>
        <div className="modal-actions">
          <button className="btn btn-outline" type="button" onClick={onCancel}>{cancelLabel}</button>
          <button className="btn btn-primary" type="button" onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  )
}
