import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prairiewealth_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from bankapp.models import TransferHistory, UserProfile

User = get_user_model()
TARGET_USER_EMAIL = 'n25257705@gmail.com' # <--- MATCHING YOUR USER

def generate():
    try:
        user = User.objects.get(username__iexact=TARGET_USER_EMAIL)
        profile = user.userprofile
        print("MATCH FOUND: Force-Dating Ledger for {}...".format(user.username))
    except User.DoesNotExist:
        print("FAILED: User '{}' NOT FOUND.".format(TARGET_USER_EMAIL))
        return

    START_DATE = datetime(2025, 8, 18)
    DAYS_DIFF = (datetime.now() - START_DATE).days
    TAX_RATE = Decimal('0.0015')

    # 1. PRIME SAVINGS CORE: 4x $20,000 SUCCESS (Total $80,000)
    for i in range(4):
        amount = Decimal('20000.00')
        random_days = random.randint(0, DAYS_DIFF - 3)
        tx_date = START_DATE + timedelta(days=random_days)
        tx_date = tx_date.replace(hour=random.randint(10, 15), minute=random.randint(0, 50))
        aware_dt = timezone.make_aware(tx_date, timezone.get_default_timezone())
        
        # Savings Credit
        tx = TransferHistory.objects.create(
            user=user, from_account="OneVanilla Corp", to_account="Prime Savings",
            amount=amount, transaction_type='Deposit', status='Completed'
        )
        # BYPASS AUTO_NOW_ADD
        TransferHistory.objects.filter(pk=tx.pk).update(timestamp=aware_dt)
        profile.savings_balance += amount
        
        # Immediate Compliance Fee (0.15% = $30.00)
        tax = (amount * TAX_RATE).quantize(Decimal('0.01'))
        tax_tx = TransferHistory.objects.create(
            user=user, from_account="Prime Savings", to_account="Federal Treasury Reserve",
            amount=tax, transaction_type='Withdrawal', status='Completed'
        )
        TransferHistory.objects.filter(pk=tax_tx.pk).update(timestamp=aware_dt)
        profile.savings_balance -= tax
        print("SUCCESS: Forced savings entry for {}.".format(tx_date.strftime('%Y-%m-%d')))

    # 2. PRIVATE CHECKING CORE: Distributed $10,000 across multiple parts
    checking_target = Decimal('10000.00')
    checking_cur = Decimal('0.00')
    while checking_cur < checking_target:
        chunk = Decimal(random.uniform(1800, 3200)).quantize(Decimal('0.01'))
        if (checking_cur + chunk) > checking_target:
            chunk = checking_target - checking_cur
            
        random_days_c = random.randint(0, DAYS_DIFF - 3)
        aware_dt_c = timezone.make_aware(START_DATE + timedelta(days=random_days_c), timezone.get_default_timezone())
        
        # Checking Credit
        tx_c = TransferHistory.objects.create(
            user=user, from_account="OneVanilla Corp", to_account="Private Checking",
            amount=chunk, transaction_type='Deposit', status='Completed'
        )
        TransferHistory.objects.filter(pk=tx_c.pk).update(timestamp=aware_dt_c)
        profile.checking_balance += chunk
        
        # Fee
        tax_c = (chunk * TAX_RATE).quantize(Decimal('0.01'))
        tax_tx_c = TransferHistory.objects.create(
            user=user, from_account="Private Checking", to_account="Federal Treasury Reserve",
            amount=tax_c, transaction_type='Withdrawal', status='Completed'
        )
        TransferHistory.objects.filter(pk=tax_tx_c.pk).update(timestamp=aware_dt_c)
        profile.checking_balance -= tax_c
        checking_cur += chunk

    # 3. AUDIT DEPTH NOISE: Mixture of PENDING and FAILED
    for j in range(8):
        random_days_n = random.randint(0, DAYS_DIFF - 3)
        aware_dt_n = timezone.make_aware(START_DATE + timedelta(days=random_days_n), timezone.get_default_timezone())
        
        tx_n = TransferHistory.objects.create(
            user=user, from_account="OneVanilla Corp", to_account="Hold Ledger",
            amount=Decimal(random.randint(5000, 25000)), transaction_type='Deposit',
            status=random.choice(['Pending', 'Failed'])
        )
        TransferHistory.objects.filter(pk=tx_n.pk).update(timestamp=aware_dt_n)

    # 4. FINAL SIGNATURE: $20,000 FAILED TRANSACTION (TODAY)
    failed_tx = TransferHistory.objects.create(
        user=user, from_account="OneVanilla Corp", to_account="Internal Protocol Bridge",
        amount=Decimal('20000.00'), transaction_type='Deposit', status='Failed'
    )
    # Today's date stays as now
    
    profile.save()
    print("FINISHED: Ledger successfully forced to 2025-2026 registry.")

if __name__ == "__main__":
    generate()
