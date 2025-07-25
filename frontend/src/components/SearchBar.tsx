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

  useEffect(() => {
    if (isSelected) {
      setIsSelected(false);
      return;
    }
    const timeout = setTimeout(async () => {
      if (query.length >= 1) { 
        if (cache[query]) {
          setResults(cache[query]);
          setShowDropdown(true);
          return;
        }
        setLoading(true);
        setShowDropdown(true); 
        try {
          const res = await onSearch(query);
          setResults(res);
          setCache(prev => ({ ...prev, [query]: res }));
        } catch (error) {
          console.error('Search error:', error);
          setResults([]);
        } finally {
          setLoading(false);
        }
      } else {
        // Clear results and hide dropdown for empty queries
        setResults([]);
        setShowDropdown(false);
        setLoading(false);
      }
    }, 800); // debounce

    return () => clearTimeout(timeout);
  }, [query]);

  const handleSelect = (result: string) => {
    onSelect(result);
    setQuery(result);
    setResults([]);
    setShowDropdown(false);
    setIsSelected(true);
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
          ) : results.length === 0 ? (
            <li className={`${baseStyle}`}>No results found</li>
          ) : (
            results.map((result, i) => (
              <li
                key={i}
                className={`${baseStyle}`}
                onClick={() => handleSelect(result)}
              >
                {result}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
