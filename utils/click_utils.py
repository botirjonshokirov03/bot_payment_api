import hashlib
import logging
import os
from typing import Dict, Any, Optional
from db import get_collection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("click_utils")

# Get Click.uz configuration from environment variables
SECRET_KEY = os.getenv("CLICK_SECRET_KEY")
SERVICE_ID = os.getenv("CLICK_SERVICE_ID")
MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID")

def verify_sign_string(data: dict, is_complete: bool = False) -> bool:
    """
    Verify Click.uz signature string with debug logging.
    """
    try:
        click_trans_id = str(data.get("click_trans_id", ""))
        service_id = str(data.get("service_id", ""))
        merchant_trans_id = str(data.get("merchant_trans_id", ""))
        amount = str(data.get("amount", ""))  # Avoid float conversion
        action = str(data.get("action", ""))
        sign_time = str(data.get("sign_time", ""))
        merchant_prepare_id = str(data.get("merchant_prepare_id", "")) if is_complete else ""

        # Construct raw string
        if is_complete:
            raw = (
                click_trans_id +
                service_id +
                SECRET_KEY +
                merchant_trans_id +
                merchant_prepare_id +
                amount +
                action +
                sign_time
            )
        else:
            raw = (
                click_trans_id +
                service_id +
                SECRET_KEY +
                merchant_trans_id +
                amount +
                action +
                sign_time
            )

        # Calculate MD5 signature
        calc_sign = hashlib.md5(raw.encode()).hexdigest()
        received_sign = data.get("sign_string", "")

        # Logging to debug signature mismatches
        logger.warning("=== Signature Debug ===")
        logger.warning(f"click_trans_id: {click_trans_id}")
        logger.warning(f"service_id: {service_id}")
        logger.warning(f"merchant_trans_id: {merchant_trans_id}")
        if is_complete:
            logger.warning(f"merchant_prepare_id: {merchant_prepare_id}")
        logger.warning(f"amount: {amount}")
        logger.warning(f"action: {action}")
        logger.warning(f"sign_time: {sign_time}")
        logger.warning(f"SECRET_KEY: {SECRET_KEY}")
        logger.warning(f"Raw String: {raw}")
        logger.warning(f"Generated MD5: {calc_sign}")
        logger.warning(f"Received Sign: {received_sign}")
        logger.warning("========================")

        return calc_sign == received_sign
    except Exception as e:
        logger.error(f"Error verifying sign_string: {str(e)}")
        return False


async def get_payment_status(merchant_trans_id: str) -> Optional[str]:
    """
    Get payment status from database
    
    Args:
        merchant_trans_id: Merchant transaction ID
        
    Returns:
        str: Payment status or None if payment not found
    """
    try:
        payments = get_collection("payments")
        payment = await payments.find_one({"merchant_trans_id": merchant_trans_id})
        
        if payment:
            return payment.get("status")
        return None
    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        return None

async def update_user_subscription(user_id: int, duration_months: int = 1) -> bool:
    """
    Update user subscription status after successful payment
    
    Args:
        user_id: Telegram user ID
        duration_months: Subscription duration in months
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        users = get_collection("users")
        
        # Get current user data
        user = await users.find_one({"user_id": user_id})
        if not user:
            logger.error(f"User {user_id} not found when updating subscription")
            return False
            
        # Calculate new subscription end date
        from datetime import datetime, timedelta
        current_date = datetime.now()
        
        # If user already has a subscription that hasn't expired, extend it
        current_end_date = user.get("subscription_end")
        if current_end_date and current_end_date > current_date:
            new_end_date = current_end_date + timedelta(days=30 * duration_months)
        else:
            new_end_date = current_date + timedelta(days=30 * duration_months)
            
        # Update user subscription
        await users.update_one(
            {"user_id": user_id},
            {"$set": {
                "has_paid_access": True,
                "subscription_end": new_end_date,
                "last_payment_date": current_date
            }}
        )
        
        logger.info(f"Updated subscription for user {user_id} until {new_end_date}")
        return True
    except Exception as e:
        logger.error(f"Error updating user subscription: {str(e)}")
        return False

async def extract_user_id_from_merchant_trans_id(merchant_trans_id: str) -> Optional[int]:
    """
    Extract user ID from merchant transaction ID
    
    Args:
        merchant_trans_id: Merchant transaction ID (format: TG_<user_id>_<timestamp>)
        
    Returns:
        int: User ID or None if extraction failed
    """
    try:
        parts = merchant_trans_id.split('_')
        if len(parts) >= 2 and parts[0] == "TG":
            return int(parts[1])
        return None
    except Exception as e:
        logger.error(f"Error extracting user ID from {merchant_trans_id}: {str(e)}")
        return None