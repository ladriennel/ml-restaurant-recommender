'use client';

import { useState } from 'react';
import Button from '@/components/Button'
import SearchBar from '@/components/SearchBar';

export default function Location() {
    const [selectedLocation, setSelectedLocation] = useState<string | null>(null);

    return (
        <div className="min-h-screen ml-8 mr-8 md:ml-32 md:mr-32 lg:ml-64 lg:mr-64 flex flex-col justify-center items-center">
            <h1 className="text-foreground-1 text-center">Taste<br />Point</h1>
            <h2 className="text-foreground-1 text-center">What do you want to eat?</h2>
            {/*Placeholder for dynamic text */}
            <h3 className="text-foreground-2 text-center pt-8 underline">
                {selectedLocation ? selectedLocation : 'Somewhere, Tasty'}
            </h3>
            <SearchBar
                placeholder="Search locations"
                onSearch={async (query) => {
                    const mockData = [
                        'Dallas, Texas',
                        'London, England',
                        'Taipei, Taiwan',
                        'New York City, New York',
                        'Brooklyn, New York',
                        'Ithaca, New York',
                        'Los Angeles, California',
                        'Paris, France',
                        'Cambridge, Massachusetts',
                        'Shanghai, China'
                    ];

                    return new Promise<string[]>((resolve) => {
                        setTimeout(() => {
                            const filtered = mockData.filter((name) =>
                                name.toLowerCase().includes(query.toLowerCase())
                            );
                            resolve(filtered.slice(0, 6));
                        }, 300); // simulate network latency
                    });
                }}
                onSelect={(location) => setSelectedLocation(location)}
            />

            {/*
                
                <SearchBar
                placeholder="Search Location"
                onSearch={async (query) => {
                // Example: call your restaurant or location API
                    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    return data.results; // assume this is string[] or adapt
                }}
            />*/}
            <div className="flex flex-col pt-12 gap-4">
                
                <Button href="/restaurants">
                    <p>Next</p>
                </Button>
                <Button href="/" variant='secondary'>
                    <p>Back</p>
                </Button>
            </div>
        </div>
    )
}