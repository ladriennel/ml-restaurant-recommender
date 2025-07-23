'use client';

import Button from '@/components/Button'
import SearchBar from '@/components/SearchBar';
import RestaurantInsert from '@/components/RestaurantInsert';

export default function Restaurants() {
    return (
        <div className="min-h-screen ml-8 mr-8 md:ml-32 md:mr-32 lg:ml-64 lg:mr-64 flex flex-col justify-center items-center">
            <h1 className="text-foreground-1 text-center">Taste<br />Point</h1>
            <h2 className="text-foreground-1 text-center">List up to 5 restaurants that are on your mind,<br />and we’ll find the best matches in your area!</h2>
            <div className="mt-8 flex flex-col gap-6">
                <RestaurantInsert />
                <RestaurantInsert />
                <RestaurantInsert />
                <RestaurantInsert />
                <RestaurantInsert />
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