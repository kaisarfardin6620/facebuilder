from twilio.rest import Client
from django.conf import settings

def send_otp_via_twilio(phone_number, otp):
    import logging
    logger = logging.getLogger('authentication')
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your verification code is: {otp}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return True
    except Exception as e:
        logger.error(f"Twilio OTP send failed for {phone_number}: {e}")
        return False