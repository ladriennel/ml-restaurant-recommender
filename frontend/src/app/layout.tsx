import React from 'react'
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Restaurant Recommender',
  description: 'A machine learning-powered restaurant discovery tool that allows users to input restaurants (globally) and receive similar recommendations in a selected city based on a variety of factors',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}