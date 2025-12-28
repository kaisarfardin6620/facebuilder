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
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return False

        data = response.json()
        entitlements = data.get('subscriber', {}).get('entitlements', {})
        
        is_active = False
        expiry = None
        product_id = "Free"
        
        for ent_id in settings.REVENUECAT_ENTITLEMENT_IDS:
            if ent_id in entitlements:
                ent_data = entitlements[ent_id]
                expires_date_str = ent_data.get('expires_date')
                
                this_is_active = False
                if expires_date_str:
                    exp_date = parse_datetime(expires_date_str)
                    if exp_date and exp_date > timezone.now():
                        this_is_active = True
                else:
                    this_is_active = True
                
                if this_is_active:
                    is_active = True
                    expiry = parse_datetime(expires_date_str) if expires_date_str else None
                    product_id = ent_data.get('product_identifier', ent_id)
                    break 
                
                product_id = ent_data.get('product_identifier', ent_id)

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