export function ErrorBanner({ title = 'Unable to load content', message }) {
  return (
    <div className="error-banner" role="alert">
      <strong>{title}</strong>
      <p>{message}</p>
    </div>
  )
}
