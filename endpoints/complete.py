from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from db import get_collection

router = APIRouter()

@router.post("/click/complete")
async def click_complete(request: Request):
    data = await request.json()

    collection = get_collection("payments")
    await collection.insert_one(data)

    return JSONResponse({
        "error": 0,
        "error_note": "Success",
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": data.get("merchant_trans_id"),
        "merchant_confirm_id": "some_confirm_id"
    })
