import time
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from db import get_collection
import logging
from utils.click_utils import verify_sign_string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("click_prepare")

router = APIRouter()

@router.post("/click/prepare")
async def click_prepare(request: Request):
    """
    Handle Click.uz prepare request
    
    This endpoint is called by Click.uz when a user initiates a payment.
    It verifies the request and creates a payment record in the database.
    """
    try:
        # Log raw request for debugging
        body = await request.body()
        logger.info(f"Received prepare request: {body}")
        
        # Parse request data
        data = await request.json()
        logger.info(f"Parsed prepare data: {data}")
        
        # Verify signature
        if not verify_sign_string(data):
            logger.warning(f"Invalid signature in prepare request: {data}")
            return JSONResponse({"error": -1, "error_note": "Invalid sign_string"})
        
        # Extract data
        merchant_trans_id = data.get("merchant_trans_id")
        click_trans_id = data.get("click_trans_id")
        amount = float(data.get("amount"))
        
        # Validate merchant_trans_id format
        if not merchant_trans_id or not merchant_trans_id.startswith("TG_"):
            logger.error(f"Invalid merchant_trans_id format: {merchant_trans_id}")
            return JSONResponse({"error": -5, "error_note": "Invalid merchant_trans_id format"})
        
        # Check if payment already exists
        payments = get_collection("payments")
        existing = await payments.find_one({"merchant_trans_id": merchant_trans_id})
        
        if existing:
            # Verify amount matches
            if existing["amount"] != amount:
                logger.warning(f"Amount mismatch: expected {existing['amount']}, got {amount}")
                return JSONResponse({"error": -2, "error_note": "Incorrect amount"})
                
            logger.info(f"Payment already exists: {merchant_trans_id}")
        else:
            # Create new payment record
            await payments.insert_one({
                "merchant_trans_id": merchant_trans_id,
                "click_trans_id": click_trans_id,
                "amount": amount,
                "status": "prepared",
                "created_at": {"$date": {"$numberLong": str(int(time.time() * 1000))}}
            })
            logger.info(f"Created new payment record: {merchant_trans_id}")
        
        # Return success response
        return JSONResponse({
            "error": 0,
            "error_note": "Success",
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": merchant_trans_id
        })
    except Exception as e:
        logger.error(f"Error in prepare endpoint: {str(e)}")
        return JSONResponse({"error": -1, "error_note": f"Internal error: {str(e)}"})