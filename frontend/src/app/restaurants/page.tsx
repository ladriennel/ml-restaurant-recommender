'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Button from '@/components/Button'
import RestaurantInsert from '@/components/RestaurantInsert';
import { Restaurant } from '@/types';
import { store } from '@/lib/store';

export default function Restaurants() {
    const router = useRouter();
    const [searchLoading, setSearchLoading] = useState(false);
    const [progressInfo, setProgressInfo] = useState({ current: 0, total: 0 });
    const [hasResults, setHasResults] = useState(false);
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
            checkResults(); // Re-check results when store updates
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

    const handleFindRestaurants = async () => {
        const currentData = store.getAllData();
        console.log('Saving to database - Location:', currentData.location);
        console.log('Saving to database - Restaurants:', currentData.restaurants);

        // Filter out null restaurants for the API call
        const validRestaurants = currentData.restaurants.filter(r => r !== null) as Restaurant[];
        console.log('Valid restaurants to save:', validRestaurants);

        if (!currentData.location) {
            alert('Please select a location first!');
            return;
        }

        if (validRestaurants.length === 0) {
            alert('Please select at least one restaurant!');
            return;
        }

        setSearchLoading(true);
        setProgressInfo({ current: 0, total: 100 });

        // Clear cached recommendations for new search
        store.clearCachedRecommendations();

        try {
            // Realistic progress for ~3+ minute process
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
                        current: Math.min(prev.current + increment, 90) // Don't go past 90% until complete
                    };
                });
            }, 2000); // Update every 2 seconds

            const response = await fetch('http://localhost:8000/api/searches', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
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

            // Store the search ID for the results page
            if (result.id) {
                store.setCurrentSearchId(result.id);
            }

            // Complete the progress
            setProgressInfo({ current: 100, total: 100 });
            
            // Small delay to show completion
            setTimeout(() => {
                setSearchLoading(false);
                router.push('/results');
            }, 500);

        } catch (error) {
            console.error('Error saving search:', error);
            setSearchLoading(false);
            alert('Failed to save search. Please try again.');
        }
    };

    return (
        <div className="min-h-screen m-12 md:ml-32 md:mr-32 flex flex-col items-center">
            <h1 className="text-foreground-1 text-center">Taste<br />Point</h1>
            <h2 className="text-foreground-1 text-center">List up to 5 restaurants that are on your mind,<br />and we'll find the best matches in your area!</h2>
            <div className="mt-8 flex flex-col gap-6">
                {selectedRestaurants.map((restaurant, index) => (
                    <RestaurantInsert
                        key={index}
                        index={index}
                        selectedRestaurant={restaurant}
                        onSelect={handleRestaurantSelect}
                    />
                ))}
            </div>
            <div className="flex flex-col pt-8 gap-4 items-center">
                <div className={`flex gap-4 ${hasResults ? 'flex-row' : 'flex-col'}`}>
                    <Button onClick={handleFindRestaurants}>
                        <p>Find Restaurants</p>
                    </Button>
                    {hasResults && (
                        <Button href="/results">
                            <p>See Results</p>
                        </Button>
                    )}
                </div>
                
                {/* Secondary action */}
                <Button href="/location" variant='secondary'>
                    <p>Edit Location</p>
                </Button>
            </div>

            {/* Loading Modal */}
            {searchLoading && (
                <div className="fixed inset-0 z-50 bg-[rgba(215,228,230,0.9)] flex flex-col gap-6 items-center justify-center">
                    <div className="text-center">
                        <h3 className="text-2xl font-bold text-foreground-1 mb-2">Finding Your Restaurant Matches!</h3>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="w-80 bg-background-1 rounded-full h-4 shadow-inner">
                        <div 
                            className="bg-gradient-to-r from-blue-500 to-purple-600 h-4 rounded-full transition-all duration-300 ease-out"
                            style={{ width: `${(progressInfo.current / progressInfo.total) * 100}%` }}
                        ></div>
                    </div>
                    
                    {/* Progress Text */}
                    <div className="text-center">
                        <p className="text-foreground-1 font-medium">
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
            )}
        </div>
    )
}