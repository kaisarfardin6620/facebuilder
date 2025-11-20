from django.contrib import admin
from .models import User, OneTimePassword

# Register the User model so you can see users in the admin panel
admin.site.register(User)

# Register OTPs (optional, good for debugging)
admin.site.register(OneTimePassword)