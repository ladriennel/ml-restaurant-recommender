import Button from '../../components/Button'

export default function Restaurants() {
    return (
        <div className="min-h-screen ml-8 mr-8 md:ml-32 md:mr-32 lg:ml-64 lg:mr-64 flex flex-col justify-center items-center">
           <h1 className="text-foreground-1 text-center">Taste<br />Point</h1>
           <h2 className="text-foreground-1 text-center">List up to 5 restaurants that are on your mind,<br />Pand we’ll find the best matches in your area!</h2>
           <div className="flex flex-col pt-4 gap-8">
                <Button href="/location" variant='secondary'>
                    <p>Edit Location</p>
                </Button>
                <Button href="/results">
                    <p>Find Restaurants!</p>
                </Button>
            </div>
        </div>
    )
}