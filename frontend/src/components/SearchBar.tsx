'use client';

import React, { useState, useRef, useEffect } from 'react';

type SearchBarProps = {
  placeholder?: string;
  onSearch: (query: string) => Promise<string[]>; // API handler should return 6 suggestions
  onSelect: (selected: string) => void;
};

export default function SearchBar({ placeholder = 'Search', onSearch, onSelect }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (query.trim() === '') {
      setSuggestions([]);
      return;
    }

    // Debounce API calls
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(async () => {
      const results = await onSearch(query);
      setSuggestions(results.slice(0, 6));
    }, 300);
  }, [query, onSearch]);

  return (
    <div className="relative w-full max-w-md pt-4">
      <input
        type="text"
        value={query}
        placeholder={placeholder}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setTimeout(() => setIsFocused(false), 150)} // delay to allow click
        className="text-base text-foreground-2 w-full h-[50px] pl-4 pr-4 pt-2 pb-2 bg-background-2 rounded-border-radius shadow-box-shadow focus:outline-none"
      />

      {isFocused && suggestions.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full bg-background-2 rounded-border-radius shadow-box-shadow overflow-y-auto">
          {suggestions.map((suggestion, index) => (
            <li
              key={index}
              className="text-base text-foreground-2 px-4 py-2 hover:bg-background-3 truncate overflow-x-auto cursor-pointer"
              onMouseDown={() => {
                setQuery(suggestion);
                setIsFocused(false);
                setSuggestions([]);
                onSelect(suggestion);
              }}
            >
              {suggestion}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
