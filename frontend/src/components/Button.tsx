'use client';

import { useRouter } from 'next/navigation';
import React from 'react';

type ButtonProps = {
  children: React.ReactNode;
  href?: string; 
  onClick?: () => void; 
  className?: string;
  variant?: 'primary' | 'secondary' | 'tertiary';
};

export default function Button({
  children,
  href,
  onClick,
  className = '',
  variant = 'primary',
}: ButtonProps) {
  const router = useRouter();

  const handleClick = () => {
    if (href) {
      router.push(href);
    } else if (onClick) {
      onClick();
    }
  };

  const baseStyles = 'text-foreground-2 transition cursor-pointer';
  const primaryStyles =
    'w-[185px] h-[50px] bg-background-2 hover:bg-background-3 rounded-border-radius shadow-box-shadow';
  const secondaryStyles = 'underline';
  const tertiaryStyles = 'w-8 h-8 bg-background-2 hover:bg-background-3 rounded-full flex items-center justify-center';

  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return primaryStyles;
      case 'secondary':
        return secondaryStyles;
      case 'tertiary':
        return tertiaryStyles;
      default:
        return primaryStyles;
    }
  };

  const combinedStyles = `${baseStyles} ${getVariantStyles()} ${className}`;

  return (
    <button onClick={handleClick} className={combinedStyles}>
      {children}
    </button>
  );
}