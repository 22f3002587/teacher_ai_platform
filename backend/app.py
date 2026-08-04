from fastapi import FastAPI
from api.upload import router as upload_router

app = FastAPI(
    title = "Teacher AI Platform"
)

app.include_router(upload_router)

@app.get("/")
def root():
    return {
        "message":"Teacher AI Platform API Running"
    }
