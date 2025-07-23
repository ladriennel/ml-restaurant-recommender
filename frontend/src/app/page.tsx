import React from 'react';
import Button from '@/components/Button'

export default function Home() {
  return (
    <main className="min-h-screen bg-background-1">
      
      <section className="min-h-screen flex flex-row">

        <div className="flex flex-col justify-center basis-1/3 pr-32 pl-32">
          <h1 className="text-foreground-1 text-right">Taste<br />Point</h1>
          <h2 className="text-foreground-1 pt-4 text-right">find the<br />restaurants<br />that suit your<br />cravings</h2>
        </div>

        <div className="flex flex-col gap-8 justify-center items-center bg-background-2 basis-2/3">
          <div className="bg-background-1 h-1/2 w-2/3 rounded-border-radius shadow-box-shadow"></div>
          <Button href="/location">
            <p>Next</p>
          </Button>
        </div>
      </section>
    </main>
  )
}