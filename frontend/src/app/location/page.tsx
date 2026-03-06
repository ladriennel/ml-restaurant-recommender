'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Button from '@/components/Button';
import SearchBar from '@/components/SearchBar';
import ProgressNav from '@/components/ProgressNav';
import { LocationData } from '@/types';
import { store } from '@/lib/store';

export default function Location() {
    const router = useRouter();
    const [locationOptions, setLocationOptions] = useState<LocationData[]>([]);
    const [selectedLocation, setSelectedLocation] = useState<LocationData | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const storedLocation = store.getLocation();
        if (storedLocation) {
            setSelectedLocation(storedLocation);
        }

        const unsubscribe = store.subscribe(() => {
            const currentLocation = store.getLocation();
            setSelectedLocation(currentLocation);
        });

        return unsubscribe;
    }, []);

    const handleLocationSelect = (selectedName: string) => {
        const matched = locationOptions.find((loc) => loc.name === selectedName);
        if (matched) {
            console.log('Selected location:', matched);
            setSelectedLocation(matched);
            store.setLocation(matched);
            setError(null);
        } else {
            console.warn('No location found for selected name');
        }
    };

    const handleNext = () => {
        if (!selectedLocation) {
            setError('Please select a city before continuing.');
            return;
        }
        router.push('/restaurants');
    };

    return (
        <main className="min-h-screen bg-background-1 flex flex-col">
            <ProgressNav />
            <section className="flex-1 flex flex-col md:flex-row">
                {/* Left: branding */}
                <div className="flex flex-col justify-center md:basis-1/3 px-8 md:px-16 py-12 md:py-0">
                    <h1 className="text-foreground-1 text-center md:text-right">Taste<br />Point</h1>
                    <h2 className="text-foreground-1 pt-4 text-center md:text-right">Where do<br />you want<br />to eat?</h2>
                </div>

                {/* Right: white panel */}
                <div className="flex flex-col justify-center items-center bg-background-2 md:basis-2/3 py-12 md:py-0 px-8">
                    <div className="w-full max-w-sm flex flex-col items-center">
                        <div className="flex items-center gap-3 mb-2 w-full justify-center">
                            <div className="h-px flex-1 bg-background-3" />
                            <h3 className={`text-center whitespace-nowrap ${selectedLocation ? 'text-accent-1' : 'text-foreground-2'}`}>
                                {selectedLocation ? selectedLocation.name : 'Somewhere, Tasty'}
                            </h3>
                            <div className="h-px flex-1 bg-background-3" />
                        </div>

                        <SearchBar
                            placeholder="Search Location"
                            onSearch={async (query) => {
                                try {
                                    const res = await fetch(`http://localhost:8000/api/locations?query=${encodeURIComponent(query)}`);
                                    if (!res.ok) throw new Error("Network error");
                                    const data: LocationData[] = await res.json();
                                    setLocationOptions(data);
                                    return data.map((loc) => loc.name);
                                } catch (err) {
                                    console.error(err);
                                    return [];
                                }
                            }}
                            onSelect={handleLocationSelect}
                        />

                        <div className="flex flex-col pt-8 gap-4 items-center w-full">
                            <p className={`text-xs text-red-400 text-center transition-opacity duration-200 ${error ? 'opacity-100' : 'opacity-0'}`}>
                                {error || '\u00A0'}
                            </p>
                            <Button onClick={handleNext}>
                                <p>Next</p>
                            </Button>
                            <Button href="/" variant='secondary'>
                                <p>Back</p>
                            </Button>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}
