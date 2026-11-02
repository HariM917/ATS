import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react';

interface AlertProps {
  type?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  children,
  className = '',
}) => {
  const styles = {
    info: {
      bg: 'bg-blue-50 border-blue-200 text-blue-900',
      icon: <Info className="w-5 h-5 text-blue-600 flex-shrink-0" />,
    },
    success: {
      bg: 'bg-emerald-50 border-emerald-200 text-emerald-900',
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />,
    },
    warning: {
      bg: 'bg-amber-50 border-amber-200 text-amber-900',
      icon: <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />,
    },
    error: {
      bg: 'bg-red-50 border-red-200 text-red-900',
      icon: <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />,
    },
  };

  const current = styles[type];

  return (
    <div className={`flex gap-3 p-4 rounded-xl border text-sm ${current.bg} ${className}`}>
      {current.icon}
      <div className="flex-1">
        {title && <h5 className="font-bold mb-0.5">{title}</h5>}
        <div>{children}</div>
      </div>
    </div>
  );
};

