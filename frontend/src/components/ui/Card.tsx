import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  children,
  hover = false,
  padding = 'md',
  className = '',
  ...props
}) => {
  const paddingStyles = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={`bg-white rounded-2xl border border-gray-100 shadow-sm transition-all duration-200 ${
        hover ? 'hover:shadow-md hover:border-gray-200' : ''
      } ${paddingStyles[padding]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

