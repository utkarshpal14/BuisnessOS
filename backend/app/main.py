from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BusinessOS AI API",
    description="Multi-agent enterprise intelligence platform API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "BusinessOS AI Backend Operational"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
