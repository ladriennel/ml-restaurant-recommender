import React from 'react';
import Button from '@/components/Button'

export default function Home() {
  return (
    <main className="min-h-screen bg-background-1">
      <section className="min-h-screen flex flex-col md:flex-row">
        <div className="flex flex-col justify-center md:basis-1/3 px-8 md:px-32 py-16 md:py-0">
          <h1 className="text-foreground-1 text-center md:text-right">Taste<br />Point</h1>
          <h2 className="text-foreground-1 pt-4 text-center md:text-right">find the<br />restaurants<br />that suit your<br />cravings</h2>
        </div>

        <div className="flex flex-col gap-8 justify-center items-center bg-background-2 md:basis-2/3 py-16 md:py-0">
          <div className="bg-background-1 w-11/12 md:h-2/3 lg:h-1/2 md:w-2/3 text-center rounded-border-radius shadow-box-shadow p-8 flex flex-col justify-center">
            <h3 className="text-foreground-1 pb-4">How It Works</h3>

            <div className="grid grid-cols-3 md:grid-cols-1 lg:grid-cols-3 gap-2 mb-6 md:mb-2 lg:mb-6">
              <div className="flex flex-col md:flex-row lg:flex-col items-center">
                <div className="text-2xl mb-2"/>
                <h2 className="text-foreground-1 mb-2 min-h-[3rem] flex items-center">Choose Location</h2>
                <h4 className="text-sm text-foreground-2 min-h-[3rem] flex items-center text-center">Select the city where you want to eat</h4>
              </div>

              <div className="flex flex-col md:flex-row lg:flex-col items-center">
                <div className="text-2xl mb-2"/>
                <h2 className="text-foreground-1 mb-2 min-h-[3rem] flex items-center">Add Favorites</h2>
                <h4 className="text-sm text-foreground-2 min-h-[3rem] flex items-center text-center">List restaurants you love from anywhere</h4>
              </div>

              <div className="flex flex-col md:flex-row lg:flex-col items-center">
                <div className="text-2xl mb-2"/>
                <h2 className="text-foreground-1 mb-2 min-h-[3rem] flex items-center">Get AI Matches</h2>
                <h4 className="text-sm text-foreground-2 min-h-[3rem] flex items-center text-center">ML algorithms find similar restaurants nearby</h4>
              </div>
            </div>

            <div>
              <h4 className="text-foreground-1 mb-2">Tech Stack</h4>
              <h4 className="text-sm text-foreground-2">
                FastAPI + Next.js • PostgreSQL • Sentence Transformers • TomTom API • Groq LLM
              </h4>
            </div>
          </div>
          
          <Button href="/location">
            <p>Next</p>
          </Button>
        </div>
      </section>
    </main>
  )
}