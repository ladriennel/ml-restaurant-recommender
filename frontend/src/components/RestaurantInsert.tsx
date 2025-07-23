'use client';

import React, { useState } from 'react';
import SearchBar from './SearchBar';
import Button from './Button';

export default function RestaurantInsert() {
    const [selectedRestaurant, setSelectedRestaurant] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleSelect = (restaurant: string) => {
        setSelectedRestaurant(restaurant);
        setIsModalOpen(false);
    };

    return (
        <>
            <div
                className="pl-4 pr-4 pt-2 pb-2 min-w-lg rounded-border-radius shadow-box-shadow bg-background-2 hover:bg-background-3 cursor-pointer transition"
                onClick={() => setIsModalOpen(true)}
            >
                {selectedRestaurant ? (
                    <p className="text-left text-foreground-2 text-base">{selectedRestaurant}</p>
                ) : (
                    <p className="text-center text-foreground-2 text-base">Choose a restaurant</p>
                )}
            </div>

            {isModalOpen && (
                <div className="fixed inset-0 z-50 bg-[rgba(215,228,230,0.8)] flex flex-col gap-68 items-center justify-center">
                    <SearchBar
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
                    />

                    <Button onClick={() => setIsModalOpen(false)}>
                        <p>Close</p>
                    </Button>
                </div>
            )}
        </>
    );
}
