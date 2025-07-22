'use client';

import { useRouter } from 'next/navigation';
import React from 'react';

type ButtonProps = {
  children: React.ReactNode;
  href?: string; // optional page route
  onClick?: () => void; // for modal or custom actions
  className?: string;
  variant?: 'primary' | 'secondary';
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
    'w-[185px] h-[50px] bg-background-2 rounded-border-radius shadow-box-shadow';
  const secondaryStyles = 'underline';

  const combinedStyles = `${baseStyles} ${variant === 'primary' ? primaryStyles : secondaryStyles
    } ${className}`;

  return (
    <button onClick={handleClick} className={combinedStyles}>
      {children}
    </button>
  );
}