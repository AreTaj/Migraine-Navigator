from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Migraine Navigator API")

# Add CORS middleware to allow requests from standard localhost ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # React default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import entries, analysis, prediction

app.include_router(entries.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(prediction.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to Migraine Navigator API"}
