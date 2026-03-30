from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import ContactMessage, UserProfile, ChatMessage, TransferHistory, RecentRecipient

def home(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('custom_admin')
    return render(request, 'bankapp/index.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Track login history
            from django.utils import timezone
            user_profile, _ = UserProfile.objects.get_or_create(user=user)
            user_profile.previous_login_at = user_profile.last_login_at
            user_profile.last_login_at = timezone.now()
            user_profile.save()

            if user.is_staff:
                return redirect('custom_admin')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid Online ID or Passcode.')
    return render(request, 'bankapp/login.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('home')

def about(request):
    return render(request, 'bankapp/about.html')

def personal(request):
    return render(request, 'bankapp/personal.html')

def business(request):
    return render(request, 'bankapp/business.html')

def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            user = User.objects.create_user(username=email, email=email, password=password, first_name=first_name, last_name=last_name)
            login(request, user)
            return redirect('dashboard')
    return render(request, 'bankapp/register.html')

@login_required(login_url='login')
def dashboard(request):
    if request.user.is_staff:
        return redirect('custom_admin')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    transfers = TransferHistory.objects.filter(user=request.user).order_by('-timestamp')[:3]
    return render(request, 'bankapp/dashboard.html', {'transfers': transfers, 'user_profile': user_profile})

@login_required(login_url='login')
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        profile_picture = request.FILES.get('profile_picture')
        
        user = request.user
        updated = False
        
        if first_name and last_name:
            user.first_name = first_name
            user.last_name = last_name
            updated = True
            
        if profile_picture:
            if user_profile.profile_picture:
                user_profile.profile_picture.delete(save=False)
            user_profile.profile_picture = profile_picture
            user_profile.save()
            updated = True
            messages.success(request, 'Your profile picture was successfully updated.')
            
        if password and len(password) >= 8:
            user.set_password(password)
            updated = True
            messages.success(request, 'Your passcode was securely updated.')
            
        if updated:
            user.save()
            update_session_auth_hash(request, user) # Kept logged in
            if not password and not profile_picture:
                messages.success(request, 'Your profile details have been updated successfully.')
            return redirect('profile')
            
    return render(request, 'bankapp/profile.html', {'user_profile': user_profile})

@login_required(login_url='login')
def verify(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_profile.verification_status = 'pending'
        user_profile.phone_number = request.POST.get('phone_number')
        user_profile.ssn = request.POST.get('ssn')
        user_profile.dob = request.POST.get('dob')
        user_profile.address_line1 = request.POST.get('address_line1')
        user_profile.city = request.POST.get('city')
        user_profile.state = request.POST.get('state')
        user_profile.zip_code = request.POST.get('zip_code')
        user_profile.occupation = request.POST.get('occupation')
        
        front = request.FILES.get('id_front')
        back = request.FILES.get('id_back')
        if front:
            user_profile.id_front = front
        if back:
            user_profile.id_back = back
            
        user_profile.save()
        messages.success(request, 'Your Identity Verification documents have been securely submitted. Please allow 2-4 hours for federal compliance review.')
        return redirect('dashboard')
    return render(request, 'bankapp/verify.html', {'user_profile': user_profile})

from decimal import Decimal

@login_required(login_url='login')
def transfer(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        from_account = request.POST.get('from_account')
        to_account = request.POST.get('to_account')
        amount_str = request.POST.get('amount')
        
        try:
            amount = Decimal(amount_str)
            if amount > 0:
                if from_account == 'checking' and to_account == 'savings':
                    if user_profile.checking_balance >= amount:
                        user_profile.checking_balance -= amount
                        user_profile.savings_balance += amount
                        user_profile.save()
                        TransferHistory.objects.create(
                            user=request.user,
                            from_account=f"Everyday Checking (...{user_profile.checking_account_number[-4:]})",
                            to_account=f"High-Yield Savings (...{user_profile.savings_account_number[-4:]})",
                            amount=amount,
                            memo=request.POST.get('memo', '')
                        )
                        messages.success(request, f'Successfully transferred ${amount:,.2f} from Checking to Savings.')
                    else:
                        messages.error(request, 'Insufficient funds in Everyday Checking.')
                elif from_account == 'savings' and to_account == 'checking':
                    if user_profile.savings_balance >= amount:
                        user_profile.savings_balance -= amount
                        user_profile.checking_balance += amount
                        user_profile.save()
                        TransferHistory.objects.create(
                            user=request.user,
                            from_account=f"High-Yield Savings (...{user_profile.savings_account_number[-4:]})",
                            to_account=f"Everyday Checking (...{user_profile.checking_account_number[-4:]})",
                            amount=amount,
                            memo=request.POST.get('memo', '')
                        )
                        messages.success(request, f'Successfully transferred ${amount:,.2f} from Savings to Checking.')
                    else:
                        messages.error(request, 'Insufficient funds in High-Yield Savings.')
                elif from_account == 'checking' and to_account == 'external':
                    if user_profile.verification_status == 'verified':
                        if user_profile.checking_balance >= amount:
                            user_profile.checking_balance -= amount
                            user_profile.save()
                            TransferHistory.objects.create(
                                user=request.user,
                                from_account=f"Checking (...{user_profile.checking_account_number[-4:]})",
                                to_account="External Wire Transfer",
                                amount=amount,
                                memo=request.POST.get('memo', '')
                            )
                            messages.success(request, f'Wire transfer of ${amount:,.2f} initiated to external bank account.')
                        else:
                            messages.error(request, 'Insufficient checking funds for wire transfer.')
                    else:
                        messages.error(request, 'You must be verified to perform external withdrawals.')
                else:
                    messages.error(request, 'Invalid transfer configuration.')
            else:
                messages.error(request, 'Transfer amount must be greater than zero.')
        except:
            messages.error(request, 'Invalid transfer amount.')
        return redirect('transfer')
        
    return render(request, 'bankapp/transfer.html', {'user_profile': user_profile})

@login_required(login_url='login')
def pay_bills(request):
    return render(request, 'bankapp/pay_bills.html')

@login_required(login_url='login')
def statements(request):
    return render(request, 'bankapp/statements.html')

@login_required(login_url='login')
def transactions(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    transfers = TransferHistory.objects.filter(user=request.user)
    return render(request, 'bankapp/transactions.html', {'user_profile': user_profile, 'transfers': transfers})

@login_required(login_url='login')
def transaction_detail(request, pk):
    from django.shortcuts import get_object_or_404
    transfer_obj = get_object_or_404(TransferHistory, pk=pk, user=request.user)
    return render(request, 'bankapp/transaction_detail.html', {'t': transfer_obj})

def legal(request):
    return render(request, 'bankapp/legal.html')

def privacy(request):
    return render(request, 'bankapp/privacy.html')

def terms(request):
    return render(request, 'bankapp/terms.html')

def security(request):
    return render(request, 'bankapp/security.html')

def fdic(request):
    return render(request, 'bankapp/fdic.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        if name and email and message:
            ContactMessage.objects.create(name=name, email=email, message=message)
            messages.success(request, 'Your message has been sent successfully! Our team will get back to you soon.')
    return render(request, 'bankapp/contact.html')

@staff_member_required(login_url='login')
def custom_admin(request):
    if not request.user.is_superuser:
        return redirect('index')
    users = User.objects.filter(is_staff=False).order_by('-date_joined')
    contact_messages = ContactMessage.objects.all().order_by('-created_at')
    
    # Group chat messages by sender
    chat_senders = User.objects.filter(sent_messages__isnull=False).distinct()
    conversations = []
    for sender in chat_senders:
        if not sender.is_superuser:
            last_message = ChatMessage.objects.filter(sender=sender).order_by('-timestamp').first()
            unread_count = ChatMessage.objects.filter(sender=sender, is_read=False).count()
            if last_message:
                conversations.append({
                    'user': sender,
                    'last_message': last_message,
                    'unread_count': unread_count
                })
    conversations.sort(key=lambda x: x['last_message'].timestamp, reverse=True)
    
    # Correct verification backlog count
    pending_users_count = UserProfile.objects.filter(verification_status='pending').count()
    
    context = {
        'users': users,
        'contact_messages': contact_messages,
        'conversations': conversations,
        'pending_users_count': pending_users_count,
    }
    return render(request, 'bankapp/custom_admin.html', context)

@staff_member_required(login_url='login')
def management_recent_messages_api(request):
    chat_senders = User.objects.filter(sent_messages__isnull=False).distinct()
    conversations = []
    for sender in chat_senders:
        if not sender.is_superuser:
            last_message = ChatMessage.objects.filter(sender=sender).order_by('-timestamp').first()
            if last_message:
                conversations.append({
                    'user_id': sender.id,
                    'username': sender.get_full_name() or sender.username,
                    'initials': sender.username[:2].upper(),
                    'profile_pic': sender.userprofile.profile_picture.url if sender.userprofile.profile_picture else None,
                    'email': sender.email,
                    'last_msg': last_message.message,
                    'time': last_message.timestamp.strftime("%b %d, %H:%M")
                })
    conversations.sort(key=lambda x: x['time'], reverse=True)
    return JsonResponse({'conversations': conversations[:10]})

@staff_member_required(login_url='login')
def verification_detail(request, user_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    profile = get_object_or_404(UserProfile, user__id=user_id)
    return render(request, 'bankapp/verification_detail.html', {'profile': profile})

@staff_member_required(login_url='login')
def all_users(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    users_list = User.objects.filter(is_staff=False).order_by('-date_joined')
    return render(request, 'bankapp/all_users.html', {
        'all_users': users_list,
        'users_count': users_list.count()
    })

@staff_member_required(login_url='login')
def verification_queue(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    pending_verifications = UserProfile.objects.filter(verification_status='pending').order_by('-user__date_joined')
    return render(request, 'bankapp/verification_queue.html', {
        'pending_users': pending_verifications,
        'pending_count': pending_verifications.count()
    })

@login_required(login_url='login')
def approve_verification(request, user_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    try:
        user_prof = UserProfile.objects.get(user__id=user_id)
        user_prof.verification_status = 'verified'
        user_prof.save()
        messages.success(request, f'Verification successfully approved for {user_prof.user.username}.')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
    return redirect('verification_queue')

@login_required(login_url='login')
def reject_verification(request, user_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    try:
        user_prof = UserProfile.objects.get(user__id=user_id)
        # Delete documents for security
        if user_prof.id_front:
            user_prof.id_front.delete(save=False)
        if user_prof.id_back:
            user_prof.id_back.delete(save=False)
        user_prof.verification_status = 'unverified'
        user_prof.save()
        messages.warning(request, f'Identity verification rejected and all digital assets purged for {user_prof.user.username}.')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
    return redirect('verification_queue')

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required
@csrf_exempt
def send_chat(request):
    if request.method == 'POST':
        try:
            msg_text = request.POST.get('message', '')
            attachment = request.FILES.get('attachment')
            
            # Handle JSON fallback for older frontend without files
            if not msg_text and not attachment and request.body:
                import json
                data = json.loads(request.body)
                msg_text = data.get('message', '')
                
            admin_target = request.POST.get('user_id') # Admin sending to specific user
            
            if msg_text or attachment:
                receiver = None
                if request.user.is_superuser and admin_target:
                    receiver = User.objects.get(id=admin_target)
                    
                ChatMessage.objects.create(
                    sender=request.user, 
                    receiver=receiver,
                    message=msg_text,
                    attachment=attachment
                )
                return JsonResponse({'status': 'ok'})
        except Exception as e:
            pass
    return JsonResponse({'status': 'error'})

@login_required
def get_chats(request):
    from django.db.models import Q
    user_id = request.GET.get('user_id')
    mark_read_param = request.GET.get('mark_read', 'false').lower() == 'true'
    
    unread_count = 0
    if request.user.is_superuser and user_id:
        target_user = User.objects.get(id=user_id)
        if mark_read_param:
            ChatMessage.objects.filter(sender=target_user, receiver=request.user, is_read=False).update(is_read=True)
        chats = ChatMessage.objects.filter(Q(sender=target_user) | Q(receiver=target_user)).order_by('timestamp')
    else:
        if mark_read_param:
            ChatMessage.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
        unread_count = ChatMessage.objects.filter(receiver=request.user, is_read=False).count()
        chats = ChatMessage.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).order_by('timestamp')
        
    data = []
    for c in chats:
        att_url = c.attachment.url if c.attachment else None
        data.append({
            'id': c.id,
            'sender': c.sender.username,
            'is_admin': c.sender.is_superuser,
            'message': c.message,
            'time': c.timestamp.strftime("%H:%M %p"),
            'is_read': c.is_read,
            'attachment': att_url
        })
    return JsonResponse({'chats': data, 'unread_count': unread_count})

@staff_member_required(login_url='login')
def admin_chat(request, user_id):
    if not request.user.is_superuser:
        return redirect('index')
    
    target_user = User.objects.get(id=user_id)
    # Mark as read
    ChatMessage.objects.filter(sender=target_user, is_read=False).update(is_read=True)
    
    if request.method == 'POST':
        msg = request.POST.get('message')
        if msg:
            ChatMessage.objects.create(sender=request.user, receiver=target_user, message=msg)
            return redirect('admin_chat', user_id=user_id)
            
    from django.db.models import Q
    messages_qs = ChatMessage.objects.filter(
        Q(sender=target_user) | Q(receiver=target_user)
    ).order_by('timestamp')

    # List of all conversations for the sidebar
    chat_senders = User.objects.filter(sent_messages__isnull=False).distinct()
    sidebar_conversations = []
    for s in chat_senders:
        if not s.is_superuser:
            last_msg = ChatMessage.objects.filter(sender=s).order_by('-timestamp').first()
            unread_cnt = ChatMessage.objects.filter(sender=s, is_read=False).count()
            if last_msg:
                sidebar_conversations.append({
                    'user': s,
                    'last_message': last_msg,
                    'unread_count': unread_cnt
                })
    sidebar_conversations.sort(key=lambda x: x['last_message'].timestamp, reverse=True)

    context = {
        'target_user': target_user,
        'messages_qs': messages_qs,
        'sidebar_conversations': sidebar_conversations,
    }
    return render(request, 'bankapp/admin_chat.html', context)

@login_required(login_url='login')
def credit_user(request):
    if not request.user.is_staff:
        return redirect('index')
    
    users = User.objects.filter(is_staff=False).order_by('username')
    recent_recipients = RecentRecipient.objects.all().order_by('-created_at')[:10]
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        amount = Decimal(request.POST.get('amount'))
        company_name = request.POST.get('company_name')
        account_type = request.POST.get('account_type') # 'checking' or 'savings'
        memo = request.POST.get('memo', 'External Deposit')
        
        target_user = User.objects.get(id=user_id)
        profile = target_user.userprofile
        
        # Original Credit
        if account_type == 'checking':
            profile.checking_balance += amount
            to_acc = f"Checking (...{profile.checking_account_number[-4:]})"
        else:
            profile.savings_balance += amount
            to_acc = f"Savings (...{profile.savings_account_number[-4:]})"
        
        # Save Transaction History for Credit
        TransferHistory.objects.create(
            user=target_user,
            from_account=company_name,
            to_account=to_acc,
            amount=amount,
            memo=memo,
            transaction_type='Deposit'
        )
        
        # IMMEDIATELY DEDUCT TAX (Fiscal Compliance Fee)
        # 2.5% Tax Rate
        tax_amount = (amount * Decimal('0.025')).quantize(Decimal('0.01'))
        if account_type == 'checking':
            profile.checking_balance -= tax_amount
        else:
            profile.savings_balance -= tax_amount
            
        profile.save()
        
        # Save Transaction History for Tax
        TransferHistory.objects.create(
            user=target_user,
            from_account=to_acc,
            to_account="Federal Treasury Reserve",
            amount=tax_amount,
            memo="Fiscal Compliance Assessment - Local ID #0947",
            transaction_type='Withdrawal',
            status='Completed'
        )
        
        # Auto-save company name
        RecentRecipient.objects.get_or_create(name=company_name)
        
        messages.success(request, f"Successfully injected ${amount} to {target_user.username}'s {account_type} ledger. A regulatory assessment of ${tax_amount} was applied.")
        return redirect('custom_admin')

    return render(request, 'bankapp/credit_user.html', {
        'users': users,
        'recent_recipients': recent_recipients
    })

@login_required(login_url='login')
def admin_credit_history(request):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    from django.db.models import Count, Sum
    
    # Get all deposits (credits) - include userprofile for profile pics
    credits = TransferHistory.objects.filter(transaction_type='Deposit').select_related('user', 'user__userprofile').order_by('-timestamp')
    
    # Statistics
    stats = {
        'total_volume': credits.aggregate(Sum('amount'))['amount__sum'] or 0,
        'count': credits.count(),
        'unique_clients': credits.values('user').distinct().count(),
    }
    
    # Group by user for the "Users Credited" list
    user_summary = User.objects.filter(transferhistory__transaction_type='Deposit').annotate(
        total_credited=Sum('transferhistory__amount'),
        credit_count=Count('transferhistory')
    ).order_by('-total_credited')

    return render(request, 'bankapp/admin_credit_history.html', {
        'credits': credits,
        'stats': stats,
        'user_summary': user_summary
    })
