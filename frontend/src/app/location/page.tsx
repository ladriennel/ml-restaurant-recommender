'use client';

import { useState, useEffect } from 'react';
import Button from '@/components/Button'
import SearchBar from '@/components/SearchBar';
import { LocationData } from '@/types';
import { store } from '@/lib/store';

export default function Location() {
    const [locationOptions, setLocationOptions] = useState<LocationData[]>([]);
    const [selectedLocation, setSelectedLocation] = useState<LocationData | null>(null);

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
        } else {
            console.warn('No location found for selected name');
        }
    };

    return (
        <div className="min-h-screen ml-8 mr-8 md:ml-32 md:mr-32 lg:ml-64 lg:mr-64 flex flex-col justify-center items-center">
            <h1 className="text-foreground-1 text-center">Taste<br />Point</h1>
            <h2 className="text-foreground-1 text-center">What do you want to eat?</h2>
            <h3 className="text-foreground-2 text-center pt-8 underline">
                {selectedLocation ? selectedLocation.name : 'Somewhere, Tasty'}
            </h3>

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