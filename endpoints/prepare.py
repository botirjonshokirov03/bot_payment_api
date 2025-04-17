from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/click/prepare")
async def click_prepare(request: Request):
    data = await request.json()

    return JSONResponse({
        "error": 0,
        "error_note": "Success",
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": data.get("merchant_trans_id"),
        "merchant_prepare_id": "some_prepare_id"
    })
