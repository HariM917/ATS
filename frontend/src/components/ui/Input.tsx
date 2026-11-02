import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  leftIcon,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || props.name || Math.random().toString(36).substring(2, 9);

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
          {label}
        </label>
      )}
      <div className="relative rounded-xl shadow-sm">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          className={`block w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-gray-900 transition-colors placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-1 ${
            leftIcon ? 'pl-10' : ''
          } ${
            error
              ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
              : 'border-gray-200 hover:border-gray-300 focus:border-indigo-500 focus:ring-indigo-100'
          } ${className}`}
          {...props}
        />
      </div>
      {error && <p className="mt-1.5 text-xs text-red-600 font-medium">{error}</p>}
      {!error && helperText && <p className="mt-1.5 text-xs text-gray-500">{helperText}</p>}
    </div>
  );
};

