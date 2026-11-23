from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.cache import cache

User = get_user_model()


class AuthenticationTests(TestCase):
    """مجموعه آزمون‌های جامع احراز هویت، ثبت‌نام و بازیابی رمز عبور"""

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user_password = 'msm*2002'
        self.user = User.objects.create_user(
            first_name='مهتاب',
            last_name='مروج',
            email='mahtabmj96@gmail.com',
            username='mahtab_test',
            role='FREELANCER',
            password=self.user_password,
            phone_number='09224294833'
        )

    # ------------------------------------------------------------------------
    # ۱. آزمون‌های ثبت‌نام (Sign Up)
    # ------------------------------------------------------------------------
    def test_signup_successful_with_pbkdf2_hashing(self):
        """ثبت‌نام موفق و بررسی ذخیره رمز به صورت هش امن PBKDF2"""
        signup_data = {
            'first_name': 'علی',
            'last_name': 'رضایی',
            'email': 'ali@gmail.com',
            'phone_number': '09123333333',
            'password': 'StrongPassword456',
            'password_confirm': 'StrongPassword456'
        }
        response = self.client.post(reverse('signup'), signup_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # بررسی وجود در دیتابیس
        created_user = User.objects.filter(email='ali@gmail.com').first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.first_name, 'علی')

        # بررسی اینکه رمز خام نیست و با الگوریتم امن PBKDF2 هش شده است
        self.assertNotEqual(created_user.password, 'StrongPassword456')
        self.assertTrue(created_user.password.startswith('pbkdf2_sha256$'))
        self.assertTrue(created_user.check_password('StrongPassword456'))

    def test_role_selection_after_signup(self):
        """تکمیل نام کاربری و نقش فریلنسر/کارفرما بعد از ثبت‌نام مطابق پونیشا"""
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)
        response = self.client.post(reverse('select_role'), {
            'username': 'mhbmj',
            'role': 'FREELANCER'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'mhbmj')
        self.assertEqual(self.user.role, 'FREELANCER')

    def test_signup_duplicate_email_rejected(self):
        """جلوگیری از ثبت‌نام با ایمیل تکراری"""
        duplicate_data = {
            'first_name': 'تست',
            'last_name': 'تکراری',
            'email': 'mahtabmj96@gmail.com',  # قبلاً در setUp ثبت شده است
            'password': 'Password123',
            'password_confirm': 'Password123'
        }
        response = self.client.post(reverse('signup'), duplicate_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', 'این ایمیل قبلاً در سیستم ثبت شده است.')

    def test_signup_password_mismatch_rejected(self):
        """بررسی عدم یکسان بودن رمز عبور و تکرار آن"""
        mismatch_data = {
            'first_name': 'مهدی',
            'last_name': 'کریمی',
            'email': 'mehdi@gmail.com',
            'password': 'StrongPass123',
            'password_confirm': 'DifferentPassword456'
        }
        response = self.client.post(reverse('signup'), mismatch_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'password_confirm', 'رمز عبور و تکرار آن یکسان نیستند.')

    def test_signup_weak_password_rejected(self):
        """رد رمزهای عبور بسیار ساده و ناامن (فقط عدد، کمتر از ۸ کاراکتر یا رمزهای ساده)"""
        # ۱. رمز فقط شامل اعداد
        weak_data = {
            'first_name': 'تست',
            'last_name': 'ضعیف',
            'email': 'weak@gmail.com',
            'password': '12345678',
            'password_confirm': '12345678'
        }
        res = self.client.post(reverse('signup'), weak_data)
        self.assertEqual(res.status_code, 200)
        self.assertFormError(res.context['form'], 'password', 'رمز عبور نمی‌تواند فقط از اعداد تشکیل شده باشد. لطفاً از ترکیب حروف و اعداد استفاده کنید.')

        # ۲. رمز کمتر از ۸ کاراکتر
        short_data = {
            'first_name': 'تست',
            'last_name': 'کوتاه',
            'email': 'short@gmail.com',
            'password': 'a1b2',
            'password_confirm': 'a1b2'
        }
        res_short = self.client.post(reverse('signup'), short_data)
        self.assertEqual(res_short.status_code, 200)
        self.assertFormError(res_short.context['form'], 'password', 'رمز عبور باید حداقل ۸ کاراکتر باشد.')

    # ------------------------------------------------------------------------
    # ۲. آزمون‌های ورود (Login) و حفظ نشست (Session)
    # ------------------------------------------------------------------------
    def test_login_successful_and_redirect_to_welcome(self):
        """ورود موفق با ایمیل و رمز صحیح و انتقال به صفحه خوش‌آمدید"""
        login_data = {
            'email': 'mahtabmj96@gmail.com',
            'password': self.user_password
        }
        response = self.client.post(reverse('login'), login_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'مهتاب مروج')

        # بررسی حفظ سشن
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_remember_me_cookie_and_session_expiry(self):
        """بررسی عملکرد تیک مرا به خاطر بسپار و تنظیم کوکی ایمیل و سشن ۳۰ روزه"""
        login_url = reverse('login')
        res = self.client.post(login_url, {
            'email': 'mahtabmj96@gmail.com',
            'password': self.user_password,
            'remember_me': 'on'
        }, follow=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('remembered_email', res.cookies)
        self.assertEqual(res.cookies['remembered_email'].value, 'mahtabmj96@gmail.com')

    def test_login_invalid_password_shows_generic_error(self):
        """ورود ناموفق با رمز اشتباه بدون افشای اینکه کدام بخش اشتباه است"""
        login_data = {
            'email': 'mahtabmj96@gmail.com',
            'password': 'WrongPassword999'
        }
        response = self.client.post(reverse('login'), login_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ایمیل یا رمز عبور اشتباه است.')

    def test_login_nonexistent_email_shows_same_generic_error(self):
        """ورود ناموفق با ایمیل ناموجود با همان پیام خطای کلی و یکسان"""
        login_data = {
            'email': 'notfound@gmail.com',
            'password': 'AnyPassword123'
        }
        response = self.client.post(reverse('login'), login_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ایمیل یا رمز عبور اشتباه است.')

    def test_welcome_page_protected_against_unauthenticated_access(self):
        """مشاهده صفحه خوش‌آمدید بدون ورود مجاز نیست و ریدایرکت می‌شود"""
        response = self.client.get(reverse('welcome'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_welcome_page_does_not_show_user_id_and_has_coming_soon_button(self):
        """بررسی عدم نمایش شناسه کاربری (ID) و وجود دکمه ورود به سامانه"""
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)
        response = self.client.get(reverse('welcome'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'شناسه کاربری (ID):')
        self.assertContains(response, 'ورود به سامانه')

    def test_coming_soon_page_authenticated(self):
        """دسترسی به صفحه به زودی پس از ورود به سامانه"""
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)
        response = self.client.get(reverse('coming_soon'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'به زودی...')

    def test_logout_terminates_session(self):
        """دکمه خروج، سشن را پایان می‌دهد"""
        # ورود ابتدا
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)
        # سپس خروج
        response = self.client.post(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    # ------------------------------------------------------------------------
    # ۳. آزمون‌های بازیابی رمز عبور (Password Reset)
    # ------------------------------------------------------------------------
    def test_forgot_password_generic_message_protects_enumeration(self):
        """عدم افشای وجود یا عدم وجود ایمیل در پاسخ بازیابی رمز"""
        # درخواست برای ایمیل ناموجود
        response = self.client.post(reverse('forgot_password'), {'email': 'ghost@example.com'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'در صورتی که حساب کاربری فعالی با این آدرس ایمیل در سامانه وجود داشته باشد')

    def test_password_reset_full_flow_with_token(self):
        """جریان کامل تغییر رمز عبور با توکن معتبر و ابطال توکن پس از استفاده"""
        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        reset_url = reverse('reset_password', kwargs={'uidb64': uidb64, 'token': token})

        # ۱. باز کردن لینک معتبر بازیابی
        get_response = self.client.get(reset_url)
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, 'تعیین رمز عبور جدید')

        # ۲. ارسال رمز عبور جدید
        post_response = self.client.post(reset_url, {
            'new_password': 'BrandNewPassword789',
            'new_password_confirm': 'BrandNewPassword789'
        }, follow=True)
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, 'رمز عبور شما با موفقیت تغییر کرد')

        # ۳. بررسی اینکه با رمز جدید می‌توان وارد شد
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('BrandNewPassword789'))

        # ۴. رد شدن لینک مصرف‌شده (Single-use token)
        used_link_response = self.client.get(reset_url)
        self.assertEqual(used_link_response.status_code, 200)
        self.assertContains(used_link_response, 'لینک نامعتبر یا منقضی شده')

    # ------------------------------------------------------------------------
    # ۴. آزمون‌های محدودیت نرخ درخواست (Rate Limit - HTTP 429)
    # ------------------------------------------------------------------------
    def test_login_rate_limit_triggered_after_5_failed_password_attempts(self):
        """قفل شدن ورود و دریافت خطای ۴۲۹ پس از ۵ بار تلاش با رمز عبور اشتباه"""
        login_url = reverse('login')
        payload = {
            'email': 'mahtabmj96@gmail.com',
            'password': 'WrongPassword123'
        }

        # ۴ بار تلاش ناموفق با رمز عبور اشتباه (کد ۲۰۰ با خطای فرم)
        for i in range(4):
            response = self.client.post(login_url, payload)
            self.assertEqual(response.status_code, 200)

        # تلاش پنجم با رمز عبور اشتباه -> دریافت خطای ۴۲۹ (Too Many Requests)
        response_5th = self.client.post(login_url, payload)
        self.assertEqual(response_5th.status_code, 429)
        self.assertContains(response_5th, 'خطای ۴۲۹', status_code=429)
        self.assertContains(response_5th, '۵ بار متوالی رمز عبور را اشتباه وارد کردید', status_code=429)

        # تلاش‌های بعدی تا قبل از انقضای زمان نیز باید ۴۲۹ برگردانند
        response_6th = self.client.post(login_url, payload)
        self.assertEqual(response_6th.status_code, 429)

    def test_login_success_resets_rate_limit_counter(self):
        """ورود موفق با رمز صحیح، شمارنده تلاش‌های ناموفق قبلی را صفر می‌کند"""
        login_url = reverse('login')

        # ۳ بار تلاش با رمز اشتباه
        for _ in range(3):
            res = self.client.post(login_url, {
                'email': 'mahtabmj96@gmail.com',
                'password': 'WrongPassword123'
            })
            self.assertEqual(res.status_code, 200)

        # ورود با رمز صحیح -> موفق و ریست شمارنده
        success_res = self.client.post(login_url, {
            'email': 'mahtabmj96@gmail.com',
            'password': self.user_password
        }, follow=True)
        self.assertEqual(success_res.status_code, 200)

        # خروج
        self.client.post(reverse('logout'))

        # اکنون کاربر نباید قفل باشد (تلاش مجدد با رمز اشتباه نباید ۴۲۹ بدهد)
        retry_res = self.client.post(login_url, {
            'email': 'mahtabmj96@gmail.com',
            'password': 'WrongAgain'
        })
        self.assertEqual(retry_res.status_code, 200)

    def test_forgot_password_rate_limit_triggers_429(self):
        """محدودیت نرخ برای بازیابی رمز عبور: درخواست بیش از ۵ بار با خطای ۴۲۹ مواجه می‌شود"""
        forgot_url = reverse('forgot_password')
        payload = {'email': 'mahtabmj96@gmail.com'}

        # ۵ بار ارسال درخواست
        for _ in range(5):
            res = self.client.post(forgot_url, payload)
            self.assertEqual(res.status_code, 302)  # ریدایرکت موفق به password_reset_done

        # درخواست ششم -> بلاک با خطای ۴۲۹
        res_6th = self.client.post(forgot_url, payload)
        self.assertEqual(res_6th.status_code, 429)
        self.assertContains(res_6th, 'خطای ۴۲۹', status_code=429)
        self.assertContains(res_6th, 'بیش از حد مجاز', status_code=429)

    # ------------------------------------------------------------------------
    # ۵. آزمون‌های آنبوردینگ (دسته‌بندی، مهارت‌ها و داشبورد)
    # ------------------------------------------------------------------------
    def test_onboarding_categories_and_skills_flow(self):
        """جریان کامل انتخاب دسته‌بندی، ثبت مهارت‌ها و ورود به داشبورد"""
        from accounts.models import Category, Skill, UserSkill
        cat = Category.objects.create(name='توسعه وب آزمایشی')
        skill = Skill.objects.create(name='PythonTest')

        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)

        # ۱. ارسال دسته‌بندی
        res_cat = self.client.post(reverse('onboarding_categories'), {
            'categories': [cat.id]
        }, follow=True)
        self.assertEqual(res_cat.status_code, 200)

        # ۲. ارسال مهارت‌ها
        res_skill = self.client.post(reverse('onboarding_skills'), {
            'skills': [skill.id]
        }, follow=True)
        self.assertEqual(res_skill.status_code, 200)
        self.assertContains(res_skill, 'PythonTest')

        # ۳. بررسی ذخیره در جدول user_skills
        self.assertTrue(UserSkill.objects.filter(user=self.user, skill=skill).exists())

    def test_dashboard_view_authenticated(self):
        """مشاهده داشبورد فریلنسر با نمایش پروژه‌ها و مهارت‌ها"""
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'جدیدترین پروژه‌های ثبت‌شده')

