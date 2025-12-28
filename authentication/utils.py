import os
from twilio.rest import Client
from django.conf import settings
import logging

logger = logging.getLogger('authentication')

def send_otp_via_twilio(phone_number):
    test_number = os.getenv('TEST_PHONE_NUMBER')
    if test_number and phone_number == test_number:
        return True

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID) \
            .verifications \
            .create(to=phone_number, channel='sms')
        return True
    except Exception as e:
        logger.error(f"Twilio Verify Send failed: {e}")
        return False

def verify_otp_via_twilio(phone_number, code):
    test_number = os.getenv('TEST_PHONE_NUMBER')
    test_otp = os.getenv('TEST_OTP_CODE')
    
    if test_number and test_otp and phone_number == test_number and code == test_otp:
        return True

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        verification_check = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID) \
            .verification_checks \
            .create(to=phone_number, code=code)

        return verification_check.status == 'approved'
    except Exception as e:
        logger.error(f"Twilio Verify Check failed: {e}")
        return False