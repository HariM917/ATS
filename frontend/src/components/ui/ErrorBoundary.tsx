import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="min-h-[400px] flex flex-col items-center justify-center p-8 text-center bg-white rounded-2xl border border-gray-100 shadow-sm max-w-md mx-auto my-12">
          <div className="w-12 h-12 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center mb-4">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-2">Something went wrong</h3>
          <p className="text-sm text-gray-500 mb-6">
            {this.state.error?.message || 'An unexpected client error occurred while rendering.'}
          </p>
          <Button
            onClick={() => this.setState({ hasError: false })}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Try Again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

