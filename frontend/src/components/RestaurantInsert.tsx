'use client';

import React, { useState } from 'react';
import SearchBar from './SearchBar';
import Button from './Button';

type Restaurant = {
    name: string;
    categories: string[];
    categorySet: number[];
    address: string;
};

type RestaurantInsertProps = {
    index: number;
    selectedRestaurant: Restaurant | null;
    onSelect: (index: number, restaurant: Restaurant) => void;
  };

export default function RestaurantInsert({
    index,
    selectedRestaurant,
    onSelect,
  }: RestaurantInsertProps) {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleSelect = (restaurantString: string) => {
        const [name, address] = restaurantString.split('\n');
        const restaurant: Restaurant = {
          name,
          address,
          categories: [],
          categorySet: [],
        };
        onSelect(index, restaurant);
        setIsModalOpen(false);
      };

    return (
        <>
            <div
                className="pl-4 pr-4 pt-2 pb-2 min-w-lg rounded-border-radius shadow-box-shadow bg-background-2 hover:bg-background-3 cursor-pointer transition"
                onClick={() => setIsModalOpen(true)}
            >
                {selectedRestaurant ? (
                    <p className="text-left text-foreground-2 text-base">{selectedRestaurant.name}</p>
                ) : (
                    <p className="text-center text-foreground-2 text-base">Choose a restaurant</p>
                )}
            </div>

            {isModalOpen && (
                <div className="fixed inset-0 z-50 pb-58 bg-[rgba(215,228,230,0.9)] flex flex-col gap-2 items-center justify-center">
                    <Button onClick={() => setIsModalOpen(false)} variant='secondary'>
                        <p>Close</p>
                    </Button>

                    {/*<SearchBar
                        placeholder="Search restaurants"
                        onSearch={async (query) => {
                            const mockData = [
                                'The French Laundry',
                                'Le Bernardin',
                                'Noma',
                                'Eleven Madison Park',
                                'Osteria Francescana',
                                'Alinea',
                                'Gaggan Anand',
                                'Blue Hill at Stone Barns',
                                'Sukiyabashi Jiro',
                                'Pujol'
                            ];

                            return new Promise<string[]>((resolve) => {
                                setTimeout(() => {
                                    const filtered = mockData.filter((name) =>
                                        name.toLowerCase().includes(query.toLowerCase())
                                    );
                                    resolve(filtered.slice(0, 6));
                                }, 300); 
                            });
                        }}
                        onSelect={handleSelect}
                    />*/}

                    <SearchBar
                        placeholder="Search restaurants"
                        onSearch={async (query) => {
                            try {
                                const res = await fetch(`http://localhost:8000/api/restaurants/search?query=${encodeURIComponent(query)}`);
                                
                                if (!res.ok) {
                                    if (res.status === 429) {
                                        throw new Error("Rate limit exceeded. Please slow down your typing.");
                                    }
                                    throw new Error(`API error: ${res.status}`);
                                }
                                
                                const restaurants: Restaurant[] = await res.json();
                                
                                // Convert restaurant objects to display strings for SearchBar
                                return restaurants.slice(0, 6).map((restaurant) => `${restaurant.name}\n${restaurant.address}`);
                                
                            } catch (err) {
                                console.error('Restaurant search error:', err);
                                // Return empty array on error so SearchBar shows "No results found"
                                return [];
                            }
                        }}
                        onSelect={handleSelect}
                    />

                    
                </div>
            )}
        </>
    );
}
