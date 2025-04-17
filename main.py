from fastapi import FastAPI
from endpoints import prepare, complete

app = FastAPI()

app.include_router(prepare.router)
app.include_router(complete.router)
