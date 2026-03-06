'use client';

import React, { useState } from 'react';
import SearchBar from './SearchBar';
import Button from './Button';
import { Restaurant } from '@/types';
import { store } from '@/lib/store';

type RestaurantInsertProps = {
    index: number;
    selectedRestaurant: Restaurant | null;
    onSelect: (index: number, restaurant: Restaurant) => void;
    onClear?: (index: number) => void;
};

export default function RestaurantInsert({
    index,
    selectedRestaurant,
    onSelect,
    onClear,
}: RestaurantInsertProps) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [restaurantOptions, setRestaurantOptions] = useState<Restaurant[]>([]);

    const handleSelect = (restaurantString: string) => {
        const [name, address] = restaurantString.split('\n');
        const fullRestaurant = restaurantOptions.find(r => r.name === name && r.address === address);

        if (fullRestaurant) {
            console.log('Selected restaurant (full data):', fullRestaurant);
            onSelect(index, fullRestaurant);
        } else {
            const basicRestaurant: Restaurant = {
                name,
                address,
                categories: [],
                categorySet: [],
            };
            console.log('Selected restaurant (fallback):', basicRestaurant);
            onSelect(index, basicRestaurant);
        }

        setIsModalOpen(false);
    };

    return (
        <>
            <div className="relative w-full">
                <div
                    className={`w-full px-4 py-3.5 rounded-border-radius border transition-all duration-200 ${
                        selectedRestaurant
                        ? 'bg-background-1 border-accent-1/50 cursor-default'
                        : 'bg-background-1 border-background-3 hover:border-accent-1/60 cursor-pointer'
                    }`}
                    onClick={selectedRestaurant ? undefined : () => setIsModalOpen(true)}
                >
                    {selectedRestaurant ? (
                        <p className="text-left text-foreground-1 text-base truncate">{selectedRestaurant.name}</p>
                    ) : (
                        <p className="text-center text-foreground-2 text-base">Choose a restaurant</p>
                    )}
                </div>

                {selectedRestaurant && onClear && (
                    <Button
                        variant="tertiary"
                        onClick={() => onClear(index)}
                        className="absolute top-1/2 right-2 -translate-y-1/2"
                    >
                        ✕
                    </Button>
                )}
            </div>

            {isModalOpen && (
                <div className="fixed inset-0 z-50 bg-[rgba(63,63,63,0.45)] flex items-start justify-center pt-16 px-4">
                    <div className="bg-background-2 rounded-border-radius shadow-box-shadow w-full max-w-sm flex flex-col">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-background-3">
                            <h3 className="text-foreground-1">Find a Restaurant</h3>
                            <Button onClick={() => setIsModalOpen(false)} variant='tertiary'>
                                ✕
                            </Button>
                        </div>

                        <div className="px-6 pt-2 pb-6 flex flex-col items-center">
                            <SearchBar
                                placeholder="Search restaurants"
                                onSearch={async (query) => {
                                    try {
                                        const location = store.getLocation();
                                        const coords = location
                                            ? `&lat=${location.latitude}&lon=${location.longitude}`
                                            : '';
                                        const res = await fetch(`http://localhost:8000/api/restaurants/search?query=${encodeURIComponent(query)}${coords}`);

                                        if (!res.ok) {
                                            if (res.status === 429) {
                                                throw new Error("Rate limit exceeded. Please slow down your typing.");
                                            }
                                            throw new Error(`API error: ${res.status}`);
                                        }

                                        const restaurants: Restaurant[] = await res.json();
                                        setRestaurantOptions(restaurants);

                                        return restaurants.slice(0, 6).map((restaurant) => `${restaurant.name}\n${restaurant.address}`);

                                    } catch (err) {
                                        console.error('Restaurant search error:', err);
                                        return [];
                                    }
                                }}
                                onSelect={handleSelect}
                            />
                            <p className="text-sm text-foreground-2 mt-4 text-center">Search for any restaurant worldwide</p>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
