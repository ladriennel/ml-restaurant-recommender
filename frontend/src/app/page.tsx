import React from 'react';

export default function Home() {
  return (
    <div className="bg-background-1">
      
      {/* Typography Testing */}
      <section className="space-y-4">
        <h1>This is H1 - Merriweather Italic 64px</h1>
        <h2>This is H2 - Merriweather Sans 20px with 2px letter spacing</h2>
        <h3>This is H3 - Average Sans 28px</h3>
        <p className="text-foreground-2">This is body text - Average Sans 20px normal weight.</p>
      </section>

      {/* Background Colors Testing */}
      <section className="space-y-4">
        <h3>Background Colors</h3>
        <div className="bg-background-1 p-4 border border-gray-300">
          <p className="text-foreground-1">Background 1 (#D7E4E6) with Foreground 1 (Black)</p>
        </div>
        <div className="bg-background-2 p-4 border border-gray-300">
          <p className="text-foreground-1">Background 2 (White) with Foreground 1 (Black)</p>
        </div>
        <div className="bg-background-3 p-4 border border-gray-300">
          <p className="text-foreground-1">Background 3 (#D9D9D9) with Foreground 1 (Black)</p>
        </div>
      </section>

      {/* Text Colors Testing */}
      <section className="bg-background-2 p-6 space-y-4">
        <h3>Text Colors</h3>
        <p className="text-foreground-1">Foreground 1 - Black text (#000000)</p>
        <p className="text-foreground-2">Foreground 2 - Gray text (#818586)</p>
      </section>

      {/* Border Radius and Shadow Testing */}
      <section className="space-y-4">
        <h3>Border Radius and Shadow</h3>
        <div className="bg-background-2 p-6 rounded-border-radius shadow-box-shadow max-w-md">
          <p className="text-foreground-1">This card has 15px border radius and custom shadow</p>
          <p className="text-foreground-2 mt-2">Shadow: 0px 0px 10px 4px rgba(0, 0, 0, 0.25)</p>
        </div>
      </section>

      {/* Mixed Examples */}
      <section className="space-y-4">
        <h3>Mixed Design Examples</h3>
        
        <div className="bg-background-3 p-6 rounded-border-radius space-y-3">
          <h2>Card Title</h2>
          <p className="text-foreground-2">This is a subtitle in gray</p>
          <p className="text-foreground-1">Regular body text in black color</p>
        </div>

        <div className="bg-background-2 p-6 rounded-border-radius sshadow-box-shadow space-y-3">
          <h3>Another Card</h3>
          <p className="text-foreground-2">Secondary text color example</p>
          <button className="bg-background-1 text-foreground-1 px-4 py-2 rounded-border-radius hover:bg-background-3 transition-colors">
            Sample Button
          </button>
        </div>
      </section>

    </div>
  )
}