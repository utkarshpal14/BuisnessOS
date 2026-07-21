from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_planner import router as planner_router

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

app.include_router(planner_router)

@app.get("/")
def read_root():
    return {"message": "BusinessOS AI Backend Operational"}
