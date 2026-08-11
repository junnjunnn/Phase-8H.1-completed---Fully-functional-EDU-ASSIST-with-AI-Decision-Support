import { InboxIcon } from '@heroicons/react/24/outline'

export function EmptyState({ title, message, actionLabel, onAction }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" aria-hidden="true">
        <InboxIcon className="icon" />
      </div>
      <h3>{title}</h3>
      <p>{message}</p>
      {actionLabel && onAction ? (
        <button type="button" className="btn btn-primary btn-sm" onClick={onAction}>{actionLabel}</button>
      ) : null}
    </div>
  )
}
