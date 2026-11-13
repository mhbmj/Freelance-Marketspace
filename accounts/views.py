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

from .models import User
from .forms import LoginForm, SignupForm, ForgotPasswordForm, ResetPasswordForm


def login_view(request):
    """صفحه ورود به سامانه"""
    if request.user.is_authenticated:
        return redirect('welcome')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)  # حفظ وضعیت سشن کاربر
            messages.success(request, f'خوش آمدید، {user.full_name}!')
            return redirect('welcome')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def signup_view(request):
    """صفحه ثبت‌نام و ایجاد حساب کاربری جدید"""
    if request.user.is_authenticated:
        return redirect('welcome')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()  # رمز به شکل هش امن PBKDF2 ذخیره می‌شود
            messages.success(
                request,
                'حساب کاربری شما با موفقیت ایجاد شد! اکنون می‌توانید با ایمیل و رمز عبور خود وارد شوید.'
            )
            return redirect('login')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


def forgot_password_view(request):
    """درخواست بازیابی رمز عبور با پیام امن و بدون افشای ایمیل"""
    if request.user.is_authenticated:
        return redirect('welcome')

    if request.method == 'POST':
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


def logout_view(request):
    """خروج از سامانه و ابطال سشن"""
    logout(request)
    messages.info(request, 'شما با موفقیت از حساب کاربری خود خارج شدید.')
    return redirect('login')
