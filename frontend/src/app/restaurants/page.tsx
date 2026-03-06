'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Button from '@/components/Button';
import RestaurantInsert from '@/components/RestaurantInsert';
import ProgressNav from '@/components/ProgressNav';
import { Restaurant } from '@/types';
import { store } from '@/lib/store';

export default function Restaurants() {
    const router = useRouter();
    const [searchLoading, setSearchLoading] = useState(false);
    const [progressInfo, setProgressInfo] = useState({ current: 0, total: 0 });
    const [hasResults, setHasResults] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedRestaurants, setSelectedRestaurants] = useState<(Restaurant | null)[]>(
        Array(5).fill(null)
    );

    useEffect(() => {
        const storedRestaurants = store.getRestaurants();
        setSelectedRestaurants(storedRestaurants);

        const checkResults = () => {
            const searchId = store.getCurrentSearchId();
            const cachedRecs = store.getCachedRecommendations();
            setHasResults(searchId !== null && cachedRecs !== null && cachedRecs.length > 0);
        };

        checkResults();

        const unsubscribe = store.subscribe(() => {
            const currentRestaurants = store.getRestaurants();
            setSelectedRestaurants(currentRestaurants);
            checkResults();
        });

        return unsubscribe;
    }, []);

    const handleRestaurantSelect = (index: number, restaurant: Restaurant) => {
        const updated = [...selectedRestaurants];
        updated[index] = restaurant;
        setSelectedRestaurants(updated);
        store.updateRestaurant(index, restaurant);

        console.log(`Updated restaurant at index ${index}:`, restaurant);
        console.log('Current selectedRestaurants:', updated);
    };

    const handleRestaurantClear = (index: number) => {
        const updated = [...selectedRestaurants];
        updated[index] = null;
        setSelectedRestaurants(updated);
        store.updateRestaurant(index, null);

        console.log(`Cleared restaurant at index ${index}`);
        console.log('Current selectedRestaurants:', updated);
    };

    const handleFindRestaurants = async () => {
        const currentData = store.getAllData();
        console.log('Saving to database - Location:', currentData.location);
        console.log('Saving to database - Restaurants:', currentData.restaurants);

        const validRestaurants = currentData.restaurants.filter(r => r !== null) as Restaurant[];
        console.log('Valid restaurants to save:', validRestaurants);

        if (!currentData.location) {
            setError('Please select a city first.');
            return;
        }

        if (validRestaurants.length === 0) {
            setError('Please add at least one restaurant.');
            return;
        }

        setError(null);

        setSearchLoading(true);
        setProgressInfo({ current: 0, total: 100 });

        store.clearCachedRecommendations();

        try {
            const progressInterval = setInterval(() => {
                setProgressInfo(prev => {
                    let increment = 1;
                    if (prev.current < 10) {
                        increment = 2;
                    } else if (prev.current < 80) {
                        increment = 1;
                    } else {
                        increment = 0.5;
                    }

                    return {
                        ...prev,
                        current: Math.min(prev.current + increment, 90)
                    };
                });
            }, 2000);

            const response = await fetch('http://localhost:8000/api/searches', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    location: currentData.location,
                    restaurants: validRestaurants,
                }),
            });

            clearInterval(progressInterval);
            console.log('Response status:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Search saved successfully:', result);

            if (result.id) {
                store.setCurrentSearchId(result.id);
            }

            setProgressInfo({ current: 100, total: 100 });

            setTimeout(() => {
                setSearchLoading(false);
                router.push('/results');
            }, 500);

        } catch (error) {
            console.error('Error saving search:', error);
            setSearchLoading(false);
            setError('Something went wrong. Please try again.');
        }
    };

    return (
        <main className="min-h-screen bg-background-1 flex flex-col">
            <ProgressNav />
            <section className="flex-1 flex flex-col md:flex-row">
                {/* Left: branding */}
                <div className="flex flex-col justify-center md:basis-1/3 px-8 md:px-16 py-12 md:py-0">
                    <h1 className="text-foreground-1 text-center md:text-right">Taste<br />Point</h1>
                    <h2 className="text-foreground-1 pt-4 text-center md:text-right">List up to 5<br />restaurants<br />on your mind</h2>
                </div>

                {/* Right: white panel */}
                <div className="flex flex-col justify-center items-center bg-background-2 md:basis-2/3 py-12 md:py-0 px-8">
                    <div className="w-full max-w-lg flex flex-col gap-3">
                        {selectedRestaurants.map((restaurant, index) => (
                            <div key={index} className="flex items-center gap-4">
                                <span
                                    className="shrink-0 text-lg font-bold w-5 text-right leading-none"
                                    style={{ fontFamily: 'Merriweather, serif', fontStyle: 'italic', color: 'var(--accent-1)' }}
                                >
                                    {index + 1}
                                </span>
                                <div className="flex-1">
                                    <RestaurantInsert
                                        index={index}
                                        selectedRestaurant={restaurant}
                                        onSelect={handleRestaurantSelect}
                                        onClear={handleRestaurantClear}
                                    />
                                </div>
                            </div>
                        ))}

                        <div className="flex flex-col pt-4 gap-4 items-center">
                            <p className={`text-xs text-red-400 text-center transition-opacity duration-200 ${error ? 'opacity-100' : 'opacity-0'}`}>
                                {error || '\u00A0'}
                            </p>
                            <div className={`flex gap-4 ${hasResults ? 'flex-row' : 'flex-col'} items-center`}>
                                <Button onClick={handleFindRestaurants}>
                                    <p>Find Restaurants</p>
                                </Button>
                                {hasResults && (
                                    <Button href="/results">
                                        <p>See Results</p>
                                    </Button>
                                )}
                            </div>
                            <Button href="/location" variant='secondary'>
                                <p>Edit Location</p>
                            </Button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Loading Modal */}
            {searchLoading && (
                <div className="fixed inset-0 z-50 bg-[rgba(63,63,63,0.45)] flex items-center justify-center p-4">
                    <div className="bg-background-1 rounded-border-radius shadow-box-shadow w-full max-w-sm p-8 flex flex-col items-center gap-5">
                        <h3 className="text-foreground-1 text-center">Finding Your<br />Restaurant Matches!</h3>

                        <div className="w-full bg-background-3 rounded-full h-1.5">
                            <div
                                className="bg-accent-1 h-1.5 rounded-full transition-all duration-300 ease-out"
                                style={{ width: `${(progressInfo.current / progressInfo.total) * 100}%` }}
                            ></div>
                        </div>

                        <div className="text-center">
                            <p className="text-foreground-1">
                                {Math.round((progressInfo.current / progressInfo.total) * 100)}% Complete
                            </p>
                            <p className="text-sm text-foreground-2 mt-1">
                                {progressInfo.current < 10 ? 'Searching city restaurants...' :
                                 progressInfo.current < 85 ? 'Processing restaurant details...' :
                                 progressInfo.current < 90 ? 'Running ML similarity analysis...' :
                                 progressInfo.current < 95 ? 'Finalizing recommendations...' :
                                 'Almost ready...'}
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}
