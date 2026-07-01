import React from 'react';
import { CheckCircle2, XCircle, Info } from 'lucide-react';

export const Button = ({ children, variant = "primary", className = "", ...props }: any) => {
  const baseStyle = "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none cursor-pointer";
  const variants: Record<string, string> = {
    primary: "bg-gradient-to-r from-indigo-600 to-indigo-700 text-white hover:shadow-lg hover:shadow-indigo-200/50 hover:-translate-y-0.5 active:translate-y-0",
    secondary: "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 hover:border-gray-300",
    ghost: "bg-transparent text-gray-600 hover:bg-gray-100 hover:text-gray-900",
    danger: "bg-red-50 text-red-600 hover:bg-red-100 border border-red-100",
    success: "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white hover:shadow-lg hover:shadow-emerald-200/50 hover:-translate-y-0.5"
  };
  return <button className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>{children}</button>;
};

export const Card = ({ children, className = "", hover = false }: any) => (
  <div className={`bg-white rounded-2xl border border-gray-100 shadow-lg shadow-gray-100/50 ${hover ? 'card-hover' : ''} ${className}`}>{children}</div>
);

export const SkeletonBlock = ({ className = "" }: { className?: string }) => (
  <div className={`skeleton ${className}`} />
);

export const SkeletonCard = () => (
  <Card className="p-6 space-y-4">
    <SkeletonBlock className="h-5 w-3/4" />
    <SkeletonBlock className="h-4 w-1/2" />
    <SkeletonBlock className="h-4 w-full" />
    <div className="flex gap-2 pt-2">
      <SkeletonBlock className="h-6 w-16 rounded-full" />
      <SkeletonBlock className="h-6 w-20 rounded-full" />
      <SkeletonBlock className="h-6 w-14 rounded-full" />
    </div>
  </Card>
);

export const EmptyState = ({ icon: Icon, title, subtitle }: { icon: any; title: string; subtitle: string }) => (
  <div className="flex flex-col items-center justify-center py-20 text-center">
    <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-4">
      <Icon className="w-10 h-10 text-gray-300" />
    </div>
    <p className="font-semibold text-gray-700 mb-1">{title}</p>
    <p className="text-sm text-gray-400">{subtitle}</p>
  </div>
);

export const ScoreBadge = ({ score, size = "sm" }: { score: number; size?: "sm" | "lg" }) => {
  const pct = Math.round(score * 100);
  const color = pct > 70 ? 'bg-emerald-500 shadow-emerald-200' : pct > 40 ? 'bg-amber-400 shadow-amber-200' : 'bg-red-400 shadow-red-200';
  const sizeClass = size === "lg" ? "px-5 py-2 text-base" : "px-3 py-1 text-xs";
  return <span className={`${sizeClass} rounded-full font-bold text-white shadow-md ${color}`}>{pct}%</span>;
};

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
          <div className="max-w-md text-center">
            <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-10 h-10 text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-gray-500 mb-6 text-sm">{this.state.error?.message}</p>
            <button
              onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition-colors"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
