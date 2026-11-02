import React from 'react';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className = '', label }) => {
  const sizeStyles = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className={`flex flex-col items-center justify-center p-4 gap-2 ${className}`}>
      <Loader2 className={`${sizeStyles[size]} animate-spin text-indigo-600`} />
      {label && <p className="text-xs font-medium text-gray-500">{label}</p>}
    </div>
  );
};

