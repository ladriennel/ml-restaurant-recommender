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
    <nav className="w-full bg-background-2 border-b border-background-3 px-6 md:px-16 py-3.5 shrink-0">
      <div className="flex items-center max-w-sm mx-auto">
        {steps.map((step, i) => (
          <div key={step.href} className={`flex items-center ${i < steps.length - 1 ? 'flex-1' : ''}`}>
            <button
              onClick={() => canNavigate(i) && router.push(step.href)}
              className={`flex items-center gap-1.5 shrink-0 transition-all duration-200 ${
                canNavigate(i) ? 'cursor-pointer' : 'cursor-default'
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
