# Tailwind CSS Design System Skill

## Purpose
Expert knowledge for building consistent, scalable design systems using Tailwind CSS with dark mode support and component-driven architecture.

## Core Design System Principles

### Color Palette Architecture
```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

export default {
  theme: {
    extend: {
      colors: {
        // Primary brand colors
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
        // Semantic colors
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        error: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        // Neutral grays with dark mode support
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
          950: '#030712',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'medium': '0 4px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'strong': '0 10px 40px -10px rgba(0, 0, 0, 0.15), 0 20px 25px -5px rgba(0, 0, 0, 0.1)',
      },
    },
  },
  darkMode: 'class',
} satisfies Config;
```

### Dark Mode Implementation
```typescript
// hooks/useTheme.ts
import { useState, useCallback, useEffect } from 'react';

interface ThemeContextType {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;
}

export const useTheme = (): ThemeContextType => {
  const [theme, setThemeState] = useState<'light' | 'dark'>(() => {
    if (typeof window === 'undefined') return 'light';
    
    const stored = localStorage.getItem('theme');
    if (stored === 'light' || stored === 'dark') return stored;
    
    return window.matchMedia('(prefers-color-scheme: dark)').matches 
      ? 'dark' 
      : 'light';
  });

  const setTheme = useCallback((newTheme: 'light' | 'dark') => {
    setThemeState(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  }, [theme, setTheme]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  return { theme, setTheme, toggleTheme };
};
```

## Component Variants System

### Button Component Variants
```typescript
import React from 'react';
import { cn } from '../utils/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const buttonVariants = {
  variant: {
    primary: 'bg-primary-600 hover:bg-primary-700 text-white shadow-sm focus:ring-primary-500',
    secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-900 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-100',
    outline: 'border border-gray-300 hover:bg-gray-50 text-gray-700 dark:border-gray-600 dark:hover:bg-gray-800 dark:text-gray-300',
    ghost: 'hover:bg-gray-100 text-gray-700 dark:hover:bg-gray-800 dark:text-gray-300',
    danger: 'bg-error-600 hover:bg-error-700 text-white shadow-sm focus:ring-error-500',
  },
  size: {
    sm: 'px-3 py-1.5 text-sm font-medium rounded-md',
    md: 'px-4 py-2 text-sm font-medium rounded-md',
    lg: 'px-6 py-3 text-base font-medium rounded-lg',
    xl: 'px-8 py-4 text-lg font-medium rounded-lg',
  },
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  leftIcon,
  rightIcon,
  children,
  className,
  disabled,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  const variantClasses = buttonVariants.variant[variant];
  const sizeClasses = buttonVariants.size[size];
  
  return (
    <button
      className={cn(
        baseClasses,
        variantClasses,
        sizeClasses,
        loading && 'cursor-not-allowed opacity-75',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {leftIcon && !loading && <span className="mr-2">{leftIcon}</span>}
      {children}
      {rightIcon && <span className="ml-2">{rightIcon}</span>}
    </button>
  );
};

Button.displayName = 'Button';
```

### Input Component System
```typescript
import React from 'react';
import { cn } from '../utils/cn';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  variant?: 'default' | 'filled' | 'outline';
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  variant = 'default',
  className,
  id,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  
  const baseInputClasses = 'block w-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    default: 'border border-gray-300 rounded-md px-3 py-2 bg-white dark:bg-gray-900 dark:border-gray-600',
    filled: 'border-0 rounded-md px-3 py-2 bg-gray-100 dark:bg-gray-800',
    outline: 'border-2 border-gray-200 rounded-lg px-3 py-2 bg-transparent dark:border-gray-700',
  };
  
  const errorClasses = error 
    ? 'border-error-300 focus:border-error-500 focus:ring-error-500' 
    : 'focus:border-primary-500';
  
  return (
    <div className="space-y-1">
      {label && (
        <label 
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          {label}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-400 dark:text-gray-500">{leftIcon}</span>
          </div>
        )}
        
        <input
          id={inputId}
          className={cn(
            baseInputClasses,
            variantClasses[variant],
            errorClasses,
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            className
          )}
          {...props}
        />
        
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <span className="text-gray-400 dark:text-gray-500">{rightIcon}</span>
          </div>
        )}
      </div>
      
      {(error || helperText) && (
        <p className={cn(
          'text-sm',
          error ? 'text-error-600 dark:text-error-400' : 'text-gray-500 dark:text-gray-400'
        )}>
          {error || helperText}
        </p>
      )}
    </div>
  );
};

Input.displayName = 'Input';
```

## Layout Components

### Card Component System
```typescript
import React from 'react';
import { cn } from '../utils/cn';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'bordered' | 'elevated' | 'flat';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
}

export const Card: React.FC<CardProps> = ({
  variant = 'default',
  padding = 'md',
  className,
  children,
  ...props
}) => {
  const variantClasses = {
    default: 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg',
    bordered: 'bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-xl',
    elevated: 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-medium',
    flat: 'bg-gray-50 dark:bg-gray-800 rounded-lg',
  };
  
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
    xl: 'p-8',
  };
  
  return (
    <div
      className={cn(
        variantClasses[variant],
        paddingClasses[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div 
    className={cn('flex items-center justify-between pb-4 border-b border-gray-200 dark:border-gray-700', className)}
    {...props}
  >
    {children}
  </div>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div className={cn('pt-4', className)} {...props}>
    {children}
  </div>
);

Card.displayName = 'Card';
CardHeader.displayName = 'CardHeader';
CardContent.displayName = 'CardContent';
```

### Grid System and Responsive Utilities
```typescript
import React from 'react';
import { cn } from '../utils/cn';

interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
  gap?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  responsive?: {
    sm?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
    md?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
    lg?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
    xl?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
  };
}

export const Grid: React.FC<GridProps> = ({
  cols = 1,
  gap = 'md',
  responsive,
  className,
  children,
  ...props
}) => {
  const gapClasses = {
    none: 'gap-0',
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
    xl: 'gap-8',
  };
  
  const colClasses = {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    5: 'grid-cols-5',
    6: 'grid-cols-6',
    12: 'grid-cols-12',
  };
  
  const responsiveClasses = responsive ? Object.entries(responsive)
    .map(([breakpoint, cols]) => `${breakpoint}:${colClasses[cols]}`)
    .join(' ') : '';
  
  return (
    <div
      className={cn(
        'grid',
        colClasses[cols],
        gapClasses[gap],
        responsiveClasses,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

Grid.displayName = 'Grid';
```

## Animation and Transition Utilities

### Transition Components
```typescript
import React from 'react';
import { cn } from '../utils/cn';

interface FadeTransitionProps {
  show: boolean;
  children: React.ReactNode;
  className?: string;
}

export const FadeTransition: React.FC<FadeTransitionProps> = ({
  show,
  children,
  className
}) => {
  return (
    <div
      className={cn(
        'transition-all duration-300 ease-in-out',
        show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2 pointer-events-none',
        className
      )}
    >
      {children}
    </div>
  );
};

export const SlideTransition: React.FC<FadeTransitionProps> = ({
  show,
  children,
  className
}) => {
  return (
    <div
      className={cn(
        'transition-all duration-300 ease-in-out overflow-hidden',
        show ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0',
        className
      )}
    >
      {children}
    </div>
  );
};

FadeTransition.displayName = 'FadeTransition';
SlideTransition.displayName = 'SlideTransition';
```

## Accessibility and Performance

### Focus Management
```typescript
import { useCallback } from 'react';

export const useFocusManagement = () => {
  const focusableElementsSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  
  const trapFocus = useCallback((element: HTMLElement) => {
    const focusableElements = element.querySelectorAll(focusableElementsSelector);
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
    
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };
    
    element.addEventListener('keydown', handleKeyDown);
    firstElement?.focus();
    
    return () => {
      element.removeEventListener('keydown', handleKeyDown);
    };
  }, []);
  
  return { trapFocus };
};
```

### Performance Monitoring
```typescript
import { useEffect, useRef } from 'react';

export const usePerformanceMonitor = (componentName: string): number => {
  const renderCount = useRef(0);
  const startTime = useRef(performance.now());
  
  useEffect(() => {
    renderCount.current += 1;
    const endTime = performance.now();
    const renderTime = endTime - startTime.current;
    
    if (renderTime > 16) { // More than one frame
      console.warn(`${componentName} render took ${renderTime.toFixed(2)}ms (render #${renderCount.current})`);
    }
    
    startTime.current = performance.now();
  });
  
  return renderCount.current;
};
```

#[[file:frontend/tailwind.config.ts]]
#[[file:frontend/src/hooks/useTheme.ts]]
#[[file:frontend/src/components/ui/Button.tsx]]