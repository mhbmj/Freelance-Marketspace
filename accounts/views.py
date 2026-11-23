from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib import messages
from django.conf import settings

from .models import User, Category, Skill, UserSkill, Project, Proposal
from .forms import LoginForm, SignupForm, ForgotPasswordForm, ResetPasswordForm, RoleSelectionForm
from .rate_limit import (
    is_login_rate_limited,
    record_login_failed_attempt,
    reset_login_attempts,
    check_forgot_password_rate_limit,
)


def home_view(request):
    """صفحه اصلی و لندینگ پیج پلتفرم فریلنسری (Home Page)"""
    latest_projects = Project.objects.filter(status='OPEN').order_by('-created_at')[:4]

    initials = "MA"
    if request.user.is_authenticated and request.user.first_name and request.user.last_name:
        initials = (request.user.first_name[0] + request.user.last_name[0]).upper()

    return render(request, 'accounts/home.html', {
        'latest_projects': latest_projects,
        'user_initials': initials,
    })


def login_view(request):
    """صفحه ورود با پشتیبانی از قابلیت 'مرا به خاطر بسپار' و محدودیت نرخ درخواست"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    remembered_email = request.COOKIES.get('remembered_email', 'mahtabmj96@gmail.com')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        remember_me = request.POST.get('remember_me')

        # ۱. بررسی اینکه آیا کاربر قبلاً به دلیل ۵ بار اشتباه در رمز عبور قفل شده است
        if is_login_rate_limited(email):
            return render(request, 'accounts/429.html', {
                'message': 'به دلیل ۵ بار ورود رمز عبور اشتباه، دسترسی شما موقتاً مسدود شده است.',
                'wait_minutes': 5
            }, status=429)

        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            reset_login_attempts(email)  # ریست شمارنده در ورود موفق
            login(request, user)  # حفظ وضعیت سشن کاربر

            # قابلیت «مرا به خاطر بسپار»: تنظیم طول عمر نشست
            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 30)  # ذخیره ۳۰ روزه
            else:
                request.session.set_expiry(0)  # انقضا با بستن مرورگر

            messages.success(request, f'خوش آمدید، {user.full_name}!')

            if not user.username or not user.role:
                response = redirect('select_role')
            else:
                response = redirect('dashboard')

            # ذخیره یا تمدید کوکی ایمیل برای پیشنهاد خودکار در ورودهای بعدی
            if remember_me:
                response.set_cookie('remembered_email', user.email, max_age=60 * 60 * 24 * 30)

            return response
        else:
            # فقط در صورتی که کاربر در سیستم وجود داشته باشد و رمز اشتباه زده شود (کنترل Rate Limit فقط برای پسورد)
            if email and User.objects.filter(email=email).exists():
                attempts = record_login_failed_attempt(email)
                if attempts >= 5:
                    return render(request, 'accounts/429.html', {
                        'message': 'شما ۵ بار متوالی رمز عبور را اشتباه وارد کردید. دسترسی به مدت ۵ دقیقه مسدود گردید.',
                        'wait_minutes': 5
                    }, status=429)
    else:
        initial_data = {}
        if remembered_email:
            initial_data['email'] = remembered_email
        form = LoginForm(initial=initial_data)

    return render(request, 'accounts/login.html', {
        'form': form,
        'remembered_email': remembered_email,
    })


def signup_view(request):
    """صفحه ثبت‌نام و هدایت به تکمیل نام کاربری و نقش فریلنسر/کارفرما"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()  # رمز به شکل هش امن PBKDF2 ذخیره می‌شود
            login(request, user)  # لاگین خودکار بعد از ثبت‌نام
            return redirect('select_role')  # هدایت مستقیم به صفحه انتخاب نام کاربری و نقش
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def select_role_view(request):
    """صفحه تکمیل حساب کاربری و انتخاب نقش فریلنسر / کارفرما مطابق پونیشا"""
    user = request.user
    if request.method == 'POST':
        form = RoleSelectionForm(request.POST, user=user)
        if form.is_valid():
            user.username = form.cleaned_data['username']
            user.role = form.cleaned_data['role']
            user.save()
            if user.role == 'FREELANCER':
                messages.success(request, 'لطفاً حوزه‌های فعالیت و تخصص‌های خود را مشخص نمایید.')
                return redirect('onboarding_categories')
            else:
                messages.success(request, 'حساب کارفرما فعال گردید! به داشبورد خوش آمدید.')
                return redirect('dashboard')
    else:
        form = RoleSelectionForm(user=user, initial={
            'username': user.username or '',
            'role': user.role or 'FREELANCER',
        })

    return render(request, 'accounts/select_role.html', {'form': form, 'user': user})


@login_required
def onboarding_categories_view(request):
    """مرحله ۱ از ۲: انتخاب حوزه‌های فعالیت فریلنسر (Multi-select)"""
    categories = Category.objects.all().order_by('id')
    if request.method == 'POST':
        selected_ids = request.POST.getlist('categories')
        if not selected_ids:
            messages.error(request, 'لطفاً حداقل یک حوزه فعالیت را انتخاب نمایید.')
        else:
            request.session['selected_categories'] = selected_ids
            return redirect('onboarding_skills')

    selected_ids = request.session.get('selected_categories', [])
    return render(request, 'accounts/onboarding_categories.html', {
        'categories': categories,
        'selected_ids': [int(x) for x in selected_ids if str(x).isdigit()]
    })


@login_required
def onboarding_skills_view(request):
    """مرحله ۲ از ۲: انتخاب مهارت‌های تخصصی با باکس جستجوی زنده"""
    skills = Skill.objects.all().order_by('name')
    user = request.user

    if request.method == 'POST':
        selected_skill_ids = request.POST.getlist('skills')
        if not selected_skill_ids:
            messages.error(request, 'لطفاً حداقل یک مهارت را انتخاب کنید.')
        else:
            # ذخیره در دیتابیس در جدول user_skills
            UserSkill.objects.filter(user=user).delete()
            for s_id in selected_skill_ids:
                try:
                    skill_obj = Skill.objects.get(id=s_id)
                    UserSkill.objects.create(user=user, skill=skill_obj, years_of_experience=1)
                except Skill.DoesNotExist:
                    pass

            messages.success(request, 'مهارت‌های شما با موفقیت ثبت شد و حساب کاربری تکمیل گردید!')
            return redirect('dashboard')

    user_skills_ids = list(UserSkill.objects.filter(user=user).values_list('skill_id', flat=True))
    return render(request, 'accounts/onboarding_skills.html', {
        'skills': skills,
        'user_skills_ids': user_skills_ids
    })


@login_required
def dashboard_view(request):
    """داشبورد اصلی پلتفرم فریلنسری منطبق با ساختار پونیشا و تم پاستلی"""
    user = request.user
    user_skills = UserSkill.objects.filter(user=user).select_related('skill')

    projects = Project.objects.filter(status='OPEN').order_by('-created_at')

    # جستجوی زنده در پروژه‌ها
    query = request.GET.get('q', '').strip()
    if query:
        projects = projects.filter(title__icontains=query)

    # تب فعال (پروژه‌های من / پیشنهادات / محصولات)
    active_tab = request.GET.get('tab', 'my_projects')
    active_subtab = request.GET.get('subtab', 'active')

    user_proposals = Proposal.objects.filter(freelancer=user).select_related('project')
    if active_subtab == 'active':
        user_proposals = user_proposals.filter(status__in=['PENDING', 'ACCEPTED'])
    elif active_subtab == 'inactive':
        user_proposals = user_proposals.filter(status__in=['REJECTED', 'WITHDRAWN'])

    # محاسبه اینیشیال آواتار (مانند MA در پونیشا)
    initials = "MA"
    if user.first_name and user.last_name:
        initials = (user.first_name[0] + user.last_name[0]).upper()

    # محاسبه درصد تکمیل پروفایل
    profile_percent = 30
    if user.username:
        profile_percent += 20
    if user_skills.exists():
        profile_percent += 30
    if user.phone_number:
        profile_percent += 20

    return render(request, 'accounts/dashboard.html', {
        'user': user,
        'user_skills': user_skills,
        'projects': projects,
        'user_proposals': user_proposals,
        'query': query,
        'active_tab': active_tab,
        'active_subtab': active_subtab,
        'user_initials': initials,
        'profile_percent': profile_percent,
        'remaining_proposals': 5,
        'remaining_days': 0,
    })


@login_required
def welcome_view(request):
    """ریدایرکت به داشبورد اصلی"""
    return redirect('dashboard')


def forgot_password_view(request):
    """درخواست بازیابی رمز عبور با محدودیت نرخ درخواست (Rate Limit - HTTP 429) و پیام امن"""
    if request.user.is_authenticated:
        return redirect('welcome')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()

        # بررسی محدودیت نرخ ۵ بار درخواست برای بازیابی رمز عبور
        if email and check_forgot_password_rate_limit(request, email):
            return render(request, 'accounts/429.html', {
                'message': 'تعداد درخواست‌های بازیابی رمز عبور بیش از حد مجاز (۵ درخواست) بوده است.',
                'wait_minutes': 5
            }, status=429)

        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()

            dev_reset_link = None
            if user:
                # تولید توکن اختصاصی، زمان‌دار و یک‌بار مصرف
                token = default_token_generator.make_token(user)
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(
                    reverse('reset_password', kwargs={'uidb64': uidb64, 'token': token})
                )
                dev_reset_link = reset_url

                # ارسال ایمیل به کنسول جهت تست در محیط توسعه
                email_subject = 'بازیابی رمز عبور در سامانه فریلنسری'
                email_body = f"""با سلام {user.first_name} عزیز،
جهت تعیین رمز عبور جدید برای حساب کاربری خود، روی لینک زیر کلیک کنید:
{reset_url}

این لینک تا ۳۰ دقیقه معتبر بوده و تنها یک‌بار قابل استفاده است.
اگر شما این درخواست را نداده‌اید، این پیام را نادیده بگیرید."""

                send_mail(
                    subject=email_subject,
                    message=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )

            # پیام خنثی طبق نیازمندی: نباید وجود یا عدم وجود ایمیل را افشا کند
            request.session['reset_email_sent'] = True
            request.session['dev_reset_link'] = dev_reset_link if settings.DEBUG else None
            return redirect('password_reset_done')
    else:
        form = ForgotPasswordForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


def password_reset_done_view(request):
    """صفحه تأیید ارسال درخواست بازیابی رمز عبور"""
    dev_reset_link = request.session.pop('dev_reset_link', None)
    return render(request, 'accounts/password_reset_done.html', {
        'dev_reset_link': dev_reset_link
    })


def reset_password_confirm_view(request, uidb64, token):
    """فرم تعیین رمز عبور جدید با اعتبارسنجی لینک و توکن"""
    user = None
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # بررسی صحت و عدم انقضا یا مصرف قبلی توکن
    if user is None or not default_token_generator.check_token(user, token):
        return render(request, 'accounts/reset_password_invalid.html')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            # ذخیره امن رمز عبور جدید با الگوریتم PBKDF2
            user.set_password(new_password)
            user.save()
            reset_login_attempts(user.email)  # رفع قفل احتمالی حساب
            messages.success(
                request,
                'رمز عبور شما با موفقیت تغییر کرد! اکنون می‌توانید با رمز جدید وارد شوید.'
            )
            return redirect('login')
    else:
        form = ResetPasswordForm()

    return render(request, 'accounts/reset_password.html', {'form': form, 'user_target': user})


@login_required
def welcome_view(request):
    """صفحه موقت خوش‌آمدید پس از ورود موفق با حفظ وضعیت نشست"""
    return render(request, 'accounts/welcome.html', {
        'user': request.user
    })


@login_required
def coming_soon_view(request):
    """صفحه موقت به زودی برای فازهای بعدی پلتفرم"""
    return render(request, 'accounts/coming_soon.html', {
        'user': request.user
    })


def logout_view(request):
    """خروج از سامانه و ابطال سشن"""
    logout(request)
    messages.info(request, 'شما با موفقیت از حساب کاربری خود خارج شدید.')
    return redirect('login')
