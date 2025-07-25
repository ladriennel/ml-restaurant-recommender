from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import location

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In dev only, use env origin in prod (origins)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(location.router, prefix="/api")
