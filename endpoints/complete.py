from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from db import get_collection
import logging
import time
from utils.click_utils import verify_sign_string, update_user_subscription, extract_user_id_from_merchant_trans_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("click_complete")

router = APIRouter()

@router.post("/click/complete")
async def click_complete(request: Request):
    """
    Handle Click.uz complete request
    
    This endpoint is called by Click.uz after a payment is completed.
    It verifies the request, updates the payment status, and grants access to the user.
    """
    try:
        # Log raw request for debugging
        body = await request.body()
        logger.info(f"Received complete request: {body}")
        
        # Parse request data
        try:
            data = await request.json()
        except Exception:
            form_data = await request.body()
            from urllib.parse import parse_qs
            data = {k: v[0] for k, v in parse_qs(form_data.decode()).items()}

        logger.info(f"Parsed complete data: {data}")
        
        # Verify signature
        if not verify_sign_string(data, is_complete=True):
            logger.warning(f"Invalid signature in complete request: {data}")
            return JSONResponse({"error": -1, "error_note": "Invalid sign_string"})
        
        # Extract data
        merchant_trans_id = data.get("merchant_trans_id")
        click_trans_id = data.get("click_trans_id")
        click_paydoc_id = data.get("click_paydoc_id")
        
        # Find payment in database
        payments = get_collection("payments")
        payment = await payments.find_one({"merchant_trans_id": merchant_trans_id})
        
        if not payment:
            logger.error(f"Payment not found: {merchant_trans_id}")
            return JSONResponse({"error": -5, "error_note": "Payment not found"})
        
        # Check if payment is already completed
        if payment.get("status") == "completed":
            logger.info(f"Payment already completed: {merchant_trans_id}")
            return JSONResponse({
                "error": 0,
                "error_note": "Success (already completed)",
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": merchant_trans_id
            })
        
        # Update payment status
        await payments.update_one(
            {"merchant_trans_id": merchant_trans_id},
            {"$set": {
                "status": "completed", 
                "click_paydoc_id": click_paydoc_id,
                "completed_at": {"$date": {"$numberLong": str(int(time.time() * 1000))}}
            }}
        )
        logger.info(f"Updated payment status to completed: {merchant_trans_id}")
        
        # Extract user ID from merchant_trans_id and update subscription
        user_id = await extract_user_id_from_merchant_trans_id(merchant_trans_id)
        if user_id:
            success = await update_user_subscription(user_id)
            if success:
                logger.info(f"Updated subscription for user {user_id}")
            else:
                logger.error(f"Failed to update subscription for user {user_id}")
        else:
            logger.error(f"Could not extract user ID from {merchant_trans_id}")
        
        # Return success response
        return JSONResponse({
            "error": 0,
            "error_note": "Success",
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": merchant_trans_id
        })
    except Exception as e:
        logger.error(f"Error in complete endpoint: {str(e)}")
        return JSONResponse({"error": -1, "error_note": f"Internal error: {str(e)}"})