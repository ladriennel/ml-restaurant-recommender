'use client';

import React, { useState, useRef, useEffect } from 'react';

type SearchBarProps = {
  placeholder?: string;
  onSearch: (query: string) => Promise<string[]>;
  onSelect: (selected: string) => void;
};

export default function SearchBar({ placeholder = 'Search', onSearch, onSelect }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isSelected, setIsSelected] = useState(false);
  const [cache, setCache] = useState<Record<string, string[]>>({});
  const [error, setError] = useState<string | null>(null);

  const currentRequestRef = useRef<number>(0);

  useEffect(() => {
    if (isSelected) {
      setIsSelected(false);
      return;
    }
    const timeout = setTimeout(async () => {
      if (query.length >= 1) { 
        setError(null);

        if (cache[query]) {
          setResults(cache[query]);
          setShowDropdown(true);
          return;
        }

        setLoading(true);
        setShowDropdown(true); 

        const requestId = ++currentRequestRef.current;
        try {
          const res = await onSearch(query);
          if (requestId === currentRequestRef.current) {
            setResults(res);
            setCache(prev => ({ ...prev, [query]: res }));
            setError(null);
          }
        } catch (error) {
          if (requestId === currentRequestRef.current) {
            console.error('Search error:', error);
            const errorMessage = error instanceof Error ? error.message : 'Search failed';
            setError(errorMessage);
            setResults([]);
          }
        } finally {
          if (requestId === currentRequestRef.current) {
            setLoading(false);
          }
        }
      } else {
        // Clear results and hide dropdown for empty queries
        setResults([]);
        setShowDropdown(false);
        setLoading(false);
        setError(null);
        currentRequestRef.current++;
      }
    }, 800); // debounce

    return () => clearTimeout(timeout);
  }, [query, cache, onSearch]);

  const handleSelect = (result: string) => {
    onSelect(result);
    setQuery('');
    setResults([]);
    setShowDropdown(false);
    setIsSelected(true);
    setError(null);
  };

  const baseStyle = 'text-base text-foreground-2 px-4 py-2 hover:bg-background-3 truncate overflow-x-auto cursor-pointer';

  return (
    <div className="relative w-full max-w-md pt-4">
      <input
        type="text"
        value={query}
        placeholder={placeholder}
        onChange={(e) => {
          setQuery(e.target.value)
          if (isSelected) setIsSelected(false);
        }}
        className="text-base text-foreground-2 w-full h-[50px] pl-4 pr-4 pt-2 pb-2 bg-background-2 rounded-border-radius shadow-box-shadow focus:outline-none"
      />

      {showDropdown && query.length >= 1 && (
        <ul className="absolute z-10 mt-1 w-full bg-background-2 rounded-border-radius shadow-box-shadow overflow-y-auto">
          {loading ? (
            <li className={`${baseStyle}`}>Loading</li>
          ) : error ? (
            <li className={`${baseStyle} text-red-500`}>{error}</li>
          ) : results.length === 0 ? (
            <li className={`${baseStyle}`}>No results found</li>
          ) : (
            results.map((result, i) => (
              <li
                key={i}
                className={`${baseStyle}`}
                onClick={() => handleSelect(result)}
              >
                
                  {result.includes('\n') ? (
                    <>
                      <div className="font-bold truncate">{result.split('\n')[0]}</div>
                      <div className="text-sm truncate">{result.split('\n')[1]}</div>
                    </>
                  ) : (
                    result
                  )}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
