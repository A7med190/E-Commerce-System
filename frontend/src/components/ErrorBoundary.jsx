import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="container page" style={{ textAlign: 'center', paddingTop: 80 }}>
          <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 12 }}>Something went wrong</h1>
          <p className="muted" style={{ marginBottom: 24 }}>
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
