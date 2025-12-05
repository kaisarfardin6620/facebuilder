import requests
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from dashboard.models import Subscription

def verify_subscription_status(user):
    try:
        sub = Subscription.objects.filter(user=user).first()

        if sub and sub.is_active:
            if sub.expiry_date:
                if sub.expiry_date > timezone.now():
                    return True
                else:
                    sub.is_active = False
                    sub.save()
                    return False
            
            return True

    except Exception:
        return False

    return False

def manual_sync_revenuecat(user):
    app_user_id = user.phone_number
    url = f"https://api.revenuecat.com/v1/subscribers/{app_user_id}"
    
    headers = {
        "Authorization": f"Bearer {settings.REVENUECAT_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False

        data = response.json()
        entitlements = data.get('subscriber', {}).get('entitlements', {})
        target_entitlement = entitlements.get(settings.REVENUECAT_ENTITLEMENT_ID, {})
        
        is_active = False
        expiry = None
        product_id = "Unknown"
        
        if target_entitlement:
            product_id = target_entitlement.get('product_identifier', 'Premium')
            expires_date_str = target_entitlement.get('expires_date')
            
            if expires_date_str:
                expiry = parse_datetime(expires_date_str)
                if expiry and expiry > timezone.now():
                    is_active = True
            else:
                is_active = True

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'is_active': is_active,
                'expiry_date': expiry,
                'plan_name': product_id,
                'last_checked': timezone.now()
            }
        )
        return is_active

    except Exception as e:
        print(f"RevenueCat Sync Error: {e}")
        return False