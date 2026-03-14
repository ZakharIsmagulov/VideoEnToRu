from fastapi import FastAPI
from app.routes.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)
