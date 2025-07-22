import Button from '../../components/Button'

export default function Location() {
    return (
        <div className="min-h-screen ml-8 mr-8 md:ml-32 md:mr-32 lg:ml-64 lg:mr-64 flex flex-col justify-center items-center">
            <h1 className="text-foreground-1 text-center">Taste<br />Point</h1>
            <h2 className="text-foreground-1 text-center">What do you want to eat?</h2>
            {/*Placeholder for dynamic text */}
            <h3 className="text-foreground-2 text-center pt-8 underline">Somwhere, Tasty</h3>
            <div className="flex flex-col pt-4 gap-8">
                <Button href="/" variant='secondary'>
                    <p>Back</p>
                </Button>
                <Button href="/restaurants">
                    <p>Next</p>
                </Button>
            </div>
        </div>
    )
}