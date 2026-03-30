from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

import random

def generate_account_number():
    return str(random.randint(1000000000, 9999999999))

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    checking_account_number = models.CharField(max_length=10, default=generate_account_number)
    savings_account_number = models.CharField(max_length=10, default=generate_account_number)
    checking_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    savings_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    savings_apy = models.DecimalField(max_digits=5, decimal_places=2, default=4.25)
    
    # USA Standard KYC Fields
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    ssn = models.CharField(max_length=11, blank=True, null=True) # Usually hashed in production, but plaintext for this demo
    dob = models.DateField(blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    citizenship = models.CharField(max_length=100, default='United States')
    occupation = models.CharField(max_length=100, blank=True, null=True)
    
    verification_status = models.CharField(max_length=20, default='unverified') # 'unverified', 'pending', 'verified'
    id_front = models.FileField(upload_to='verification_docs/', null=True, blank=True)
    id_back = models.FileField(upload_to='verification_docs/', null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    previous_login_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE, null=True, blank=True) # Admin receiver handles all null usually or specific user
    message = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class RecentRecipient(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TransferHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_account = models.CharField(max_length=50)
    to_account = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    memo = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Completed')
    transaction_type = models.CharField(max_length=20, default='Transfer') # 'Transfer', 'Deposit', 'Withdrawal'

    class Meta:
        ordering = ['-timestamp']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except Exception:
        UserProfile.objects.create(user=instance)
