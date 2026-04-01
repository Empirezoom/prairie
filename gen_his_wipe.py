import os
import django

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prairiewealth_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from bankapp.models import TransferHistory, UserProfile

User = get_user_model()

# =================================================================
# TARGET ACCOUNT: NINA (WIPING PREVIOUS FAILED RUNS)
# =================================================================
TARGET_USER_EMAIL = 'n25257705@gmail.com'
# =================================================================

def wipe_Nina_data():
    try:
        user = User.objects.get(username__iexact=TARGET_USER_EMAIL)
        profile = user.userprofile
        
        # 1. Total Purge of related History (Deposits, Withdrawals, Transfers)
        # This clears both the User Dashboard and the Admin Audit Registry
        total_history = TransferHistory.objects.filter(user=user)
        h_count = total_history.count()
        total_history.delete()
        
        # 2. Hard-Reset Balances to $0.00
        profile.checking_balance = 0.00
        profile.savings_balance = 0.00
        profile.save()
        
        print("SUCCESS: Erased {} history entries for {}.".format(h_count, TARGET_USER_EMAIL))
        print("SUCCESS: Nina's Private Checking & Prime Savings are now $0.00.")
        
    except User.DoesNotExist:
        print("FAILED: User '{}' not found in registry.".format(TARGET_USER_EMAIL))

if __name__ == "__main__":
    wipe_Nina_data()
