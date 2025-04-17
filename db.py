import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

def get_collection(name: str):
    return db[name]
