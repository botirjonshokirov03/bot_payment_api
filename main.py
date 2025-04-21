from fastapi import FastAPI
from endpoints import prepare, complete

app = FastAPI()

# Include the routes
app.include_router(prepare.router)
app.include_router(complete.router)

@app.get("/")
async def root():
    return {"message": "Click Payment API is running"}
