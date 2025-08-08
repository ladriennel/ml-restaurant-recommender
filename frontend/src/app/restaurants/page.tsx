'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Button from '@/components/Button'
import RestaurantInsert from '@/components/RestaurantInsert';
import { Restaurant } from '@/types';
import { store } from '@/lib/store';

export default function Restaurants() {
    const router = useRouter();
    const [selectedRestaurants, setSelectedRestaurants] = useState<(Restaurant | null)[]>(
        Array(5).fill(null)
    );

    useEffect(() => {
        const storedRestaurants = store.getRestaurants();
        setSelectedRestaurants(storedRestaurants);

        const unsubscribe = store.subscribe(() => {
            const currentRestaurants = store.getRestaurants();
            setSelectedRestaurants(currentRestaurants);
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
        try {
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

            // Navigate to results page
            router.push('/results');
        } catch (error) {
            console.error('Error saving search:', error);
            alert('Failed to save search. Please try again.');
        }
    };

    return (
        <div className="min-h-screen ml-8 mr-8 md:ml-32 md:mr-32 lg:ml-64 lg:mr-64 flex flex-col justify-center items-center">
            <h1 className="text-foreground-1 text-center">Taste<br />Point</h1>
            <h2 className="text-foreground-1 text-center">List up to 5 restaurants that are on your mind,<br />and we’ll find the best matches in your area!</h2>
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
            <div className="flex flex-col pt-8 gap-4">
                <Button onClick={handleFindRestaurants}>
                    <p>Find Restaurants!</p>
                </Button>
                <Button href="/location" variant='secondary'>
                    <p>Edit Location</p>
                </Button>
            </div>
        </div>
    )
}