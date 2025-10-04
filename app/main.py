from fastapi import FastAPI

app = FastAPI(
    title="FastAPI Boilerplate",
    description="FastAPI + Docker",
    version="1.0.0"
)


@app.get("/")
def read_root():
    return {
        "message": "Witaj wariacik! API działa jak należy 🚀",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
