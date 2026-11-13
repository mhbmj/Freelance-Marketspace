from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()


class AuthenticationTests(TestCase):
    """مجموعه آزمون‌های جامع احراز هویت، ثبت‌نام و بازیابی رمز عبور"""

    def setUp(self):
        self.client = Client()
        self.user_password = 'ValidPassword123'
        self.user = User.objects.create_user(
            first_name='سارا',
            last_name='احمدی',
            email='sara@gmail.com',
            password=self.user_password,
            phone_number='09122222222'
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

    def test_signup_duplicate_email_rejected(self):
        """جلوگیری از ثبت‌نام با ایمیل تکراری"""
        duplicate_data = {
            'first_name': 'تست',
            'last_name': 'تکراری',
            'email': 'sara@gmail.com',  # قبلاً در setUp ثبت شده است
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
            'password': 'Password123',
            'password_confirm': 'DifferentPassword456'
        }
        response = self.client.post(reverse('signup'), mismatch_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'password_confirm', 'رمز عبور و تکرار آن یکسان نیستند.')

    # ------------------------------------------------------------------------
    # ۲. آزمون‌های ورود (Login) و حفظ نشست (Session)
    # ------------------------------------------------------------------------
    def test_login_successful_and_redirect_to_welcome(self):
        """ورود موفق با ایمیل و رمز صحیح و انتقال به صفحه خوش‌آمدید"""
        login_data = {
            'email': 'sara@gmail.com',
            'password': self.user_password
        }
        response = self.client.post(reverse('login'), login_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'خوش آمدید، سارا احمدی!')

        # بررسی حفظ سشن
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_invalid_password_shows_generic_error(self):
        """ورود ناموفق با رمز اشتباه بدون افشای اینکه کدام بخش اشتباه است"""
        login_data = {
            'email': 'sara@gmail.com',
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

    def test_logout_terminates_session(self):
        """دکمه خروج، سشن را پایان می‌دهد"""
        # ورود ابتدا
        self.client.login(email='sara@gmail.com', password=self.user_password)
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
