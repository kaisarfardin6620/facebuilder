import httpx
from django.conf import settings
from asgiref.sync import sync_to_async
from dashboard.models import Subscription
from django.utils.dateparse import parse_datetime
from django.utils import timezone

async def verify_subscription_status(user):
    try:
        local_sub = await Subscription.objects.filter(user=user).afirst()

        if local_sub:
            if local_sub.is_active and local_sub.expiry_date:
                if local_sub.expiry_date > timezone.now():
                    return True

            if not local_sub.is_active and local_sub.last_checked:
                time_since = timezone.now() - local_sub.last_checked
                if time_since.total_seconds() < 10:
                    return False
    except Exception:
        pass

    app_user_id = str(user.id) 
    url = f"https://api.revenuecat.com/v1/subscribers/{app_user_id}"
    
    headers = {
        "Authorization": f"Bearer {settings.REVENUECAT_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                await update_local_subscription(user, False, plan_name="Free")
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

            await update_local_subscription(user, is_active, expiry, product_id)
            return is_active

        except Exception as e:
            print(f"RevenueCat Error: {e}")
            return False

@sync_to_async
def update_local_subscription(user, is_active, expiry=None, plan_name="Unknown"):
    Subscription.objects.update_or_create(
        user=user,
        defaults={
            'is_active': is_active,
            'expiry_date': expiry,
            'plan_name': plan_name,
            'last_checked': timezone.now()
        }
    )