from django.contrib import admin
from .models import ContactMessage, UserProfile, ChatMessage

admin.site.register(ContactMessage)
admin.site.register(UserProfile)
admin.site.register(ChatMessage)
