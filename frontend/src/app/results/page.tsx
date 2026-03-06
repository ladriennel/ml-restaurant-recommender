'use client';

import React, { useState, useEffect } from 'react';
import Button from '@/components/Button';
import ProgressNav from '@/components/ProgressNav';
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
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ search_id: searchId, top_k: 10 }),
                });

                console.log('ML recommendations response status:', response.status);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                console.log('ML recommendations received:', result);

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
        <main className="min-h-screen bg-background-1 flex flex-col">
            <ProgressNav />
            <div className="flex-1 py-12 px-6">
                <div className="max-w-2xl mx-auto flex flex-col">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <h1 className="text-foreground-1">Taste<br />Point</h1>
                        <h2 className="text-foreground-1 mt-4">Here are your top 10 best matched restaurant recommendations based on your location and list!</h2>
                    </div>

                    {/* Results card */}
                    <div className="bg-background-2 rounded-border-radius shadow-box-shadow border-t-4 border-accent-1 overflow-hidden">
                        {loading && (
                            <div className="p-12 text-center">
                                <p className="text-foreground-2">Loading ML recommendations...</p>
                            </div>
                        )}

                        {error && (
                            <div className="p-12 text-center">
                                <p className="text-red-400">Error: {error}</p>
                            </div>
                        )}

                        {!loading && !error && recommendations.length === 0 && (
                            <div className="p-12 text-center">
                                <p className="text-foreground-2">No recommendations found.</p>
                            </div>
                        )}

                        {!loading && !error && recommendations.length > 0 && (
                            <div>
                                {recommendations.slice(0, 10).map((rec, index) => (
                                    <div
                                        key={rec.restaurant_id}
                                        className="flex gap-5 items-start px-6 py-5 border-b border-background-3 last:border-0"
                                    >
                                        <span
                                            className="shrink-0 text-2xl font-bold leading-none mt-0.5"
                                            style={{
                                                fontFamily: 'Merriweather, serif',
                                                fontStyle: 'italic',
                                                color: index === 0 ? 'var(--accent-2)' : 'var(--accent-1)',
                                            }}
                                        >
                                            {index + 1}
                                        </span>
                                        <div className="flex-1 min-w-0">
                                            <h3 className="text-foreground-1 truncate">{rec.restaurant_name}</h3>
                                            <p className="text-sm text-foreground-2 mt-0.5">{rec.address}</p>
                                            <p className="text-sm text-foreground-1 mt-1">Similarity: {rec.similarity_score.toFixed(3)}</p>
                                            <p className="text-xs text-foreground-2 mt-1">{rec.explanation}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col pt-6 gap-4 items-center">
                        <Button href="/">
                            <p>Home</p>
                        </Button>
                        <Button href="/restaurants" variant='secondary'>
                            <p>Edit List</p>
                        </Button>
                    </div>
                </div>
            </div>
        </main>
    );
}
