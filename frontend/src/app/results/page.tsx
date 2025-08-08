'use client';

import React, { useState, useEffect } from 'react';
import Button from '@/components/Button'
import { store } from '@/lib/store';
import { RecommendationResult } from '@/types';

export default function Results() {
    const [recommendations, setRecommendations] = useState<RecommendationResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchRecommendations = async () => {
            const searchId = store.getCurrentSearchId();
            console.log('Current search ID:', searchId);
            
            if (!searchId) {
                setError('No search ID found. Create a search first.');
                setLoading(false);
                return;
            }

            // Check if we have cached recommendations first
            const cachedRecs = store.getCachedRecommendations();
            if (cachedRecs && cachedRecs.length > 0) {
                console.log('Using cached recommendations:', cachedRecs.length);
                setRecommendations(cachedRecs);
                setLoading(false);
                setError(null);
                return;
            }

            try {
                console.log(`Fetching ML recommendations for search ID: ${searchId}`);
                
                const response = await fetch('http://localhost:8000/api/recommendations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        search_id: searchId,
                        top_k: 10
                    }),
                });

                console.log('ML recommendations response status:', response.status);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                console.log('ML recommendations received:', result);
                
                // Cache the results and set state
                store.setCachedRecommendations(result);
                setRecommendations(result);
                setError(null);
            } catch (error) {
                console.error('Error fetching ML recommendations:', error);
                setError(`Failed to fetch recommendations: ${error instanceof Error ? error.message : 'Unknown error'}`);
            } finally {
                setLoading(false);
            }
        };

        fetchRecommendations();
    }, []);

    return (
        <div className="min-h-screen ml-8 mr-8 md:ml-32 md:mr-32 lg:ml-64 lg:mr-64 flex flex-col justify-center items-center">
           <h1 className="text-foreground-1 text-center">Taste<br />Point</h1>
           <h2 className="text-foreground-1 text-center">Here are 10 restaurant recommendations in order<br />of best matched based on your location and list!</h2>
           
           <div className="bg-background-2 w-3/4 min-h-[400px] mt-8 rounded-border-radius shadow-box-shadow p-6">
               {loading && (
                   <div className="text-center">
                       <p>Loading ML recommendations...</p>
                   </div>
               )}
               
               {error && (
                   <div className="text-center text-red-500">
                       <p>Error: {error}</p>
                   </div>
               )}
               
               {!loading && !error && recommendations.length === 0 && (
                   <div className="text-center">
                       <p>No recommendations found.</p>
                   </div>
               )}
               
               {!loading && !error && recommendations.length > 0 && (
                    <div className="space-y-4">
                        {recommendations.slice(0, 10).map((rec, index) => (
                            <div key={rec.restaurant_id} className="border-b pb-2">
                                <h3 className="font-bold text-foreground-1">#{index + 1}: {rec.restaurant_name}</h3>
                                <p className="text-xs text-foreground-1">{rec.address}</p>
                                <p className="text-sm text-foreground-1">Score: {rec.similarity_score.toFixed(3)}</p>
                                <p className="text-xs text-foreground-2">{rec.explanation}</p>
                            </div>
                        ))}
                    </div>
               )}
           </div>
           
           <div className="flex flex-col pt-4 gap-4">
                <Button href="/">
                    <p>Home</p>
                </Button>
                <Button href="/restaurants" variant='secondary'>
                    <p>Edit List</p>
                </Button>
            </div>
        </div>
    )
}