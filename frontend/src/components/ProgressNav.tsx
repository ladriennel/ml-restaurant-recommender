'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { store } from '@/lib/store';

const steps = [
  { label: 'Your City', href: '/location' },
  { label: 'Your Cravings', href: '/restaurants' },
  { label: 'Your Matches', href: '/results' },
];

export default function ProgressNav() {
  const router = useRouter();
  const pathname = usePathname();
  const [hasLocation, setHasLocation] = useState(false);
  const [hasResults, setHasResults] = useState(false);

  useEffect(() => {
    const update = () => {
      setHasLocation(store.getLocation() !== null);
      const searchId = store.getCurrentSearchId();
      const cachedRecs = store.getCachedRecommendations();
      setHasResults(searchId !== null && cachedRecs !== null && cachedRecs.length > 0);
    };
    update();
    return store.subscribe(update);
  }, []);

  const currentIndex = steps.findIndex(s => s.href === pathname);
  if (currentIndex === -1) return null;

  const canNavigate = (i: number): boolean => {
    if (i === currentIndex) return false;
    if (i < currentIndex) return true;
    if (i === 1) return hasLocation;
    if (i === 2) return hasResults;
    return false;
  };

  const getDotStyle = (i: number): string => {
    if (i < currentIndex) return 'bg-accent-1';
    if (i === currentIndex) return 'bg-foreground-2';
    if (canNavigate(i)) return 'bg-accent-1';
    return 'bg-foreground-2';
  };

  const getLabelStyle = (i: number): string => {
    if (i < currentIndex) return 'text-accent-1';
    if (i === currentIndex) return 'text-foreground-2 font-medium';
    if (canNavigate(i)) return 'text-accent-1';
    return 'text-foreground-2';
  };

  return (
    <nav className="w-full bg-background-2 border-b border-background-3 px-6 md:px-16 py-5 shrink-0">
      <div className="flex items-center max-w-sm mx-auto relative">
        <button
          onClick={() => router.push('/')}
          className="absolute -left-12 flex items-center justify-center w-8 h-8 rounded transition-colors duration-200 hover:bg-accent-1/10 text-foreground-2 hover:text-accent-1 cursor-pointer"
          aria-label="Home"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
            <path d="M10.707 2.293a1 1 0 0 0-1.414 0l-7 7A1 1 0 0 0 3 11h1v6a1 1 0 0 0 1 1h4v-4h2v4h4a1 1 0 0 0 1-1v-6h1a1 1 0 0 0 .707-1.707l-7-7Z" />
          </svg>
        </button>
        {steps.map((step, i) => (
          <div key={step.href} className={`flex items-center ${i < steps.length - 1 ? 'flex-1' : ''}`}>
            <button
              onClick={() => canNavigate(i) && router.push(step.href)}
              className={`flex items-center gap-1.5 shrink-0 transition-all duration-200 rounded px-2 py-1 ${
                canNavigate(i)
                  ? 'cursor-pointer hover:bg-accent-1/10'
                  : 'cursor-default'
              } ${
                !canNavigate(i) && i !== currentIndex && i > currentIndex ? 'opacity-35' : ''
              }`}
            >
              <div className={`w-2.5 h-2.5 rounded-full shrink-0 transition-colors duration-200 ${getDotStyle(i)}`} />
              <span
                className={`text-base whitespace-nowrap transition-colors duration-200 ${getLabelStyle(i)}`}
                style={{ fontFamily: 'Merriweather Sans, sans-serif', letterSpacing: '0.04em' }}
              >
                {step.label}
              </span>
            </button>

            {i < steps.length - 1 && (
              <div className="flex-1 h-px bg-background-3 mx-2 sm:mx-3" />
            )}
          </div>
        ))}
        </div>
    </nav>
  );
}
