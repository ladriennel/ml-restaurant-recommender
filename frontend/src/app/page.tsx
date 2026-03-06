import React from 'react';
import Button from '@/components/Button'

export default function Home() {
  return (
    <main className="min-h-screen bg-background-1">
      <section className="min-h-screen flex flex-col md:flex-row">
        <div className="flex flex-col justify-center md:basis-1/3 px-8 md:px-16 py-16 md:py-0">
          <h1 className="text-foreground-1 text-center md:text-right">Taste<br />Point</h1>
          <h2 className="text-foreground-1 pt-4 text-center md:text-right">find the<br />restaurants<br />that suit your<br />cravings</h2>
        </div>

        <div className="flex flex-col gap-8 justify-center items-center bg-background-2 md:basis-2/3 py-16 md:py-0">
          <div className="bg-background-1 w-11/12 md:h-2/3 lg:h-1/2 md:w-2/3 rounded-border-radius shadow-box-shadow p-8 flex flex-col justify-center border-t-4 border-accent-2">
            <h3 className="text-foreground-1 pb-6 text-center">How It Works</h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-1 lg:grid-cols-3 gap-4 mb-6 md:mb-2 lg:mb-6">
              <div className="flex flex-col items-center text-center">
                <span className="text-accent-1 text-2xl font-bold mb-2" style={{fontFamily: 'Merriweather, serif', fontStyle: 'italic'}}>01</span>
                <h2 className="text-foreground-1 mb-2 min-h-[3rem] flex items-center">Choose Location</h2>
                <h4 className="text-foreground-2 min-h-[3rem] flex items-center text-center">Select the city where you want to eat</h4>
              </div>

              <div className="flex flex-col items-center text-center">
                <span className="text-accent-1 text-2xl font-bold mb-2" style={{fontFamily: 'Merriweather, serif', fontStyle: 'italic'}}>02</span>
                <h2 className="text-foreground-1 mb-2 min-h-[3rem] flex items-center">Add Favorites</h2>
                <h4 className="text-foreground-2 min-h-[3rem] flex items-center text-center">List restaurants you love from anywhere</h4>
              </div>

              <div className="flex flex-col items-center text-center">
                <span className="text-accent-1 text-2xl font-bold mb-2" style={{fontFamily: 'Merriweather, serif', fontStyle: 'italic'}}>03</span>
                <h2 className="text-foreground-1 mb-2 min-h-[3rem] flex items-center">Get AI Matches</h2>
                <h4 className="text-foreground-2 min-h-[3rem] flex items-center text-center">ML algorithm finds similar restaurants nearby</h4>
              </div>
            </div>

            <div className="border-t border-background-3 pt-4 flex flex-wrap justify-center gap-2">
              {['Python / FastAPI', 'Next.js', 'PostgreSQL', 'Sentence Transformers'].map(tech => (
                <span key={tech} className="px-2.5 py-1 bg-background-3 rounded text-xs text-foreground-2 tracking-wide">
                  {tech}
                </span>
              ))}
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
