import { Component } from 'react'
import { ErrorBanner } from './ErrorBanner'

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
    }

    this.reset = this.reset.bind(this)
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Uncaught error in ErrorBoundary:', error, errorInfo)
  }

  reset() {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-boundary-panel">
            <h1>Something went wrong</h1>
            <p>
              We were unable to load this page. Refresh the browser or try again below. If the
              problem persists, contact your administrator.
            </p>
            {this.state.error ? (
              <ErrorBanner title="Error details" message={this.state.error.message || String(this.state.error)} />
            ) : null}
            <div className="error-boundary-actions">
              <button type="button" onClick={this.reset}>
                Try again
              </button>
              <button type="button" onClick={() => window.location.reload()}>
                Reload page
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
