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

  const baseStyles = 'transition-colors duration-200 cursor-pointer';
  const primaryStyles =
    'w-[185px] h-[50px] bg-accent-1 hover:bg-[#6ba37e] text-white rounded-border-radius font-medium tracking-wide';
  const secondaryStyles = 'text-foreground-1 underline hover:text-foreground-2';
  const tertiaryStyles = 'w-8 h-8 bg-background-3 hover:bg-[#d4c4a0] text-foreground-1 rounded-full flex items-center justify-center text-sm';

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
