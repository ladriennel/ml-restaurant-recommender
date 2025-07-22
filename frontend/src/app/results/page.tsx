import Button from '../../components/Button'

export default function Results() {
    return (
        <div className="min-h-screen ml-8 mr-8 md:ml-32 md:mr-32 lg:ml-64 lg:mr-64 flex flex-col justify-center items-center">
           <h1 className="text-foreground-1 text-center">Taste<br />Point</h1>
           <h2 className="text-foreground-1 text-center">Here are 10 restaurant recommendations in order<br />of best matched based on your location and list!</h2>
           {/*Placeholder for a component most likely */}
           <div className="bg-background-2 w-3/4 min-h-[450px] mt-8 rounded-border-radius shadow-box-shadow">

           </div>
           <div className="flex flex-col pt-4 gap-8">
                <Button href="/restaurants" variant='secondary'>
                    <p>Edit List</p>
                </Button>
                <Button href="/">
                    <p>Home</p>
                </Button>
            </div>
        </div>
    )
}