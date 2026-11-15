from django.core.cache import cache

# تنظیمات محدودیت نرخ درخواست (Rate Limit)
LOGIN_MAX_FAILED_ATTEMPTS = 5       # حداکثر ۵ بار رمز اشتباه
LOGIN_LOCKOUT_SECONDS = 300         # ۵ دقیقه قفل شدن

FORGOT_PASSWORD_MAX_ATTEMPTS = 5   # حداکثر ۵ درخواست بازیابی
FORGOT_PASSWORD_LOCKOUT_SECONDS = 300  # ۵ دقیقه محدودیت


def get_client_ip(request):
    """دریافت آدرس IP کاربر"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def get_login_failed_attempts(email):
    """شمارش دفعات رمز اشتباه برای یک حساب"""
    key = f"login_fail_{email.strip().lower()}"
    return cache.get(key, 0)


def record_login_failed_attempt(email):
    """ثبت تلاش ناموفق جدید برای رمز عبور"""
    key = f"login_fail_{email.strip().lower()}"
    current = cache.get(key, 0) + 1
    cache.set(key, current, timeout=LOGIN_LOCKOUT_SECONDS)
    return current


def reset_login_attempts(email):
    """پاک‌سازی شمارنده پس از ورود موفق با رمز صحیح"""
    key = f"login_fail_{email.strip().lower()}"
    cache.delete(key)


def is_login_rate_limited(email):
    """آیا حساب به دلیل ۵ بار اشتباه در رمز عبور قفل شده است؟"""
    return get_login_failed_attempts(email) >= LOGIN_MAX_FAILED_ATTEMPTS


def check_forgot_password_rate_limit(request, email):
    """بررسی و ثبت محدودیت ۵ درخواست برای بازیابی رمز عبور"""
    ip = get_client_ip(request)
    key = f"forgot_pw_{ip}_{email.strip().lower()}"
    attempts = cache.get(key, 0)
    if attempts >= FORGOT_PASSWORD_MAX_ATTEMPTS:
        return True
    cache.set(key, attempts + 1, timeout=FORGOT_PASSWORD_LOCKOUT_SECONDS)
    return False
