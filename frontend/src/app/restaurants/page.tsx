'use client';

import React, { useState } from 'react';
import Button from '@/components/Button'
import RestaurantInsert from '@/components/RestaurantInsert';

type Restaurant = {
    name: string;
    categories: string[];
    categorySet: number[];
    address: string;
};

export default function Restaurants() {
    const [selectedRestaurants, setSelectedRestaurants] = useState<(Restaurant | null)[]>(
        Array(5).fill(null)
    );

    const handleRestaurantSelect = (index: number, restaurant: Restaurant) => {
        const updated = [...selectedRestaurants];
        updated[index] = restaurant;
        setSelectedRestaurants(updated);
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
                <Button href="/results">
                    <p>Find Restaurants!</p>
                </Button>
                <Button href="/location" variant='secondary'>
                    <p>Edit Location</p>
                </Button>
            </div>
        </div>
    )
}