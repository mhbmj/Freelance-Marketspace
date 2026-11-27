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
        self.assertContains(response, 'ثبت سریع پروژه')

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

        # ۲. ارسال مهارت‌ها و هدایت به صفحه اصلی
        res_skill = self.client.post(reverse('onboarding_skills'), {
            'skills': [skill.id]
        }, follow=True)
        self.assertEqual(res_skill.status_code, 200)

        # ۳. بررسی ذخیره در جدول user_skills
        self.assertTrue(UserSkill.objects.filter(user=self.user, skill=skill).exists())

    def test_onboarding_skills_redirects_to_origin_page(self):
        """ویرایش مهارت از پروفایل یا داشبورد به همان صفحه مبدا بازمی‌گردد"""
        from accounts.models import Skill
        skill = Skill.objects.first() or Skill.objects.create(name='DjangoTest')
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)

        # ویرایش مهارت از صفحه پروفایل با پارامتر next=/profile/
        res_profile = self.client.post(reverse('onboarding_skills'), {
            'skills': [skill.id],
            'next': reverse('profile')
        }, follow=False)
        self.assertEqual(res_profile.status_code, 302)
        self.assertEqual(res_profile.headers.get('Location'), reverse('profile'))

        # ویرایش مهارت از صفحه داشبورد با پارامتر next=/dashboard/
        res_dash = self.client.post(reverse('onboarding_skills'), {
            'skills': [skill.id],
            'next': reverse('dashboard')
        }, follow=False)
        self.assertEqual(res_dash.status_code, 302)
        self.assertEqual(res_dash.headers.get('Location'), reverse('dashboard'))

    def test_dashboard_view_authenticated(self):
        """مشاهده داشبورد فریلنسر با نمایش پروژه‌ها و مهارت‌ها"""
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'جدیدترین پروژه‌های ثبت‌شده')

    # ------------------------------------------------------------------------
    # ۶. آزمون‌های صفحه لیست پروژه‌ها و جستجو (/projects/)
    # ------------------------------------------------------------------------
    def test_projects_list_view_and_search(self):
        """مشاهده صفحه اختصاصی پروژه‌ها، جستجو و فیلترها"""
        from accounts.models import Project
        Project.objects.create(
            employer=self.user,
            title='پروژه تست پایتون و جنگو',
            description='توضیحات تستی برای اعتبارسنجی جستجو',
            pricing_type='FIXED_PRICE',
            budget=10000000,
            status='OPEN'
        )

        # دسترسی بدون لاگین (مهمان)
        res_guest = self.client.get(reverse('projects_list'))
        self.assertEqual(res_guest.status_code, 200)
        self.assertContains(res_guest, 'پروژه‌های باز و آماده همکاری')
        self.assertContains(res_guest, 'پروژه تست پایتون و جنگو')

        # تست جستجو با کلمه کلیدی
        res_search = self.client.get(reverse('projects_list') + '?q=جنگو')
        self.assertEqual(res_search.status_code, 200)
        self.assertContains(res_search, 'پروژه تست پایتون و جنگو')

        # تست جستجو با کلمه ناموجود
        res_not_found = self.client.get(reverse('projects_list') + '?q=کلمه_کاملا_ناموجود_xyz')
        self.assertEqual(res_not_found.status_code, 200)
        self.assertContains(res_not_found, 'هیچ پروژه‌ای مطابق با فیلترهای انتخابی یافت نشد')

    def test_terms_view_accessible_for_all(self):
        """مشاهده صفحه قوانین و مقررات پلتفرم مطابق پونیشا"""
        res = self.client.get(reverse('terms'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'قوانین و مقررات سامانه فریلنسری')
        self.assertContains(res, 'سیستم پرداخت امن (صندوق امانی - Escrow)')
        self.assertContains(res, 'فرآیند حل اختلاف و داوری')

    # ------------------------------------------------------------------------
    # ۷. آزمون‌های صفحه پروفایل و ویرایش مشخصات (/profile/)
    # ------------------------------------------------------------------------
    def test_profile_view_and_updates(self):
        """مشاهده صفحه پروفایل کاربری مطابق پونیشا و ویرایش درباره من و لوکیشن"""
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)

        # ۱. مشاهده صفحه پروفایل
        res = self.client.get(reverse('profile'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'درباره من')
        self.assertContains(res, 'سوابق کاری')
        self.assertContains(res, 'سوابق تحصیلی')
        self.assertContains(res, 'نمونه‌کارها')
        self.assertContains(res, 'وضعیت پروفایل')

        # ۲. به‌روزرسانی بخش درباره من
        res_bio = self.client.post(reverse('profile'), {
            'action': 'update_bio',
            'bio': 'برنامه‌نویس فول‌استک پایتون و ری‌اکت با علاقه به هوش مصنوعی'
        }, follow=True)
        self.assertEqual(res_bio.status_code, 200)
        self.assertContains(res_bio, 'برنامه‌نویس فول‌استک پایتون')

        # ۳. به‌روزرسانی موقعیت مکانی
        res_loc = self.client.post(reverse('profile'), {
            'action': 'update_location',
            'location': 'اصفهان، ایران'
        }, follow=True)
        self.assertEqual(res_loc.status_code, 200)
        self.assertContains(res_loc, 'اصفهان، ایران')

        # ۴. افزودن سابقه کاری (مطابق تصویر ۳۹ پونیشا)
        res_exp = self.client.post(reverse('profile'), {
            'action': 'add_experience',
            'title': 'توسعه‌دهنده فرانت‌اند',
            'company': 'دیجی‌کالا',
            'start_date': '2023-01-01',
            'is_current': 'on',
            'description': 'توسعه رابط کاربری با ری‌اکت و تیلویند'
        }, follow=True)
        self.assertEqual(res_exp.status_code, 200)
        self.assertContains(res_exp, 'سابقه کاری جدید با موفقیت اضافه شد')
        self.assertContains(res_exp, 'توسعه‌دهنده فرانت‌اند')
        self.assertContains(res_exp, 'دیجی‌کالا')

        # ۵. افزودن سابقه تحصیلی (مطابق تصویر ۴۰ پونیشا)
        res_edu = self.client.post(reverse('profile'), {
            'action': 'add_education',
            'degree': 'کارشناسی مهندسی نرم‌افزار',
            'institution': 'دانشگاه صنعتی شریف',
            'start_date': '2020-09-23',
            'end_date': '2024-06-20',
            'description': 'فارغ‌التحصیل ممتاز با رتبه برتر'
        }, follow=True)
        self.assertEqual(res_edu.status_code, 200)
        self.assertContains(res_edu, 'سابقه تحصیلی جدید با موفقیت اضافه شد')
        self.assertContains(res_edu, 'کارشناسی مهندسی نرم‌افزار')
        self.assertContains(res_edu, 'دانشگاه صنعتی شریف')

        # ۶. ایجاد نمونه‌کار جامع مطابق تصاویر ۴۳ و ۴۴ پونیشا
        res_pf_get = self.client.get(reverse('portfolio_create'))
        self.assertEqual(res_pf_get.status_code, 200)
        self.assertContains(res_pf_get, 'ایجاد نمونه کار')
        self.assertContains(res_pf_get, 'عنوان نمونه کار')
        self.assertContains(res_pf_get, 'نوع سرویس')
        self.assertContains(res_pf_get, 'نقش شما')
        self.assertContains(res_pf_get, 'مهارت‌ها')
        self.assertContains(res_pf_get, 'محدوده قیمت')

        res_pf_post = self.client.post(reverse('portfolio_create'), {
            'title': 'طراحی پنل کاربری فین‌تک',
            'service_type': 'طراحی رابط کاربری UI/UX',
            'user_role': 'طراح ارشد محصول',
            'description': 'طراحی وایرفریم‌ها، پروتوتایپ و دیزاین سیستم فین‌تک',
            'skills': 'Figma, UI/UX, React',
            'tags': 'فین‌تک، داشبورد',
            'duration_number': '15',
            'duration_unit': 'روز',
            'min_price': '15000000',
            'max_price': '25000000',
            'project_url': 'https://github.com/mahtab/fintech-ui'
        }, follow=True)
        self.assertEqual(res_pf_post.status_code, 200)
        self.assertContains(res_pf_post, 'نمونه‌کار جدید با موفقیت ایجاد و ثبت گردید')
        self.assertContains(res_pf_post, 'طراحی پنل کاربری فین‌تک')
        self.assertContains(res_pf_post, 'طراح ارشد محصول')
        self.assertContains(res_pf_post, '15 روز')

    def test_avatar_upload_valid_and_invalid_formats(self):
        """آزمون آپلود تصویر پروفایل مطابق شرایط عکس ۲۰ (حجم ۵MB و فرمت‌های مجاز)"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)

        # ۱. آپلود فایل نامعتبر با فرمت txt
        invalid_file = SimpleUploadedFile("test.txt", b"not an image", content_type="text/plain")
        res_invalid = self.client.post(reverse('profile'), {
            'action': 'upload_avatar',
            'avatar_file': invalid_file
        }, follow=True)
        self.assertEqual(res_invalid.status_code, 200)
        self.assertContains(res_invalid, 'فرمت فایل معتبر نیست')

        # ۲. آپلود فایل معتبر با فرمت png
        valid_png = SimpleUploadedFile("avatar.png", b"\x89PNG\r\n\x1a\nfakeimagecontent", content_type="image/png")
        res_valid = self.client.post(reverse('profile'), {
            'action': 'upload_avatar',
            'avatar_file': valid_png
        }, follow=True)
        self.assertEqual(res_valid.status_code, 200)
        self.assertContains(res_valid, 'تصویر پروفایل شما با موفقیت ذخیره شد')

        # ۳. اطمینان از نمایش آواتار آپلود شده در سایر بخش‌ها (داشبورد، هدر، و صفحه اصلی)
        res_dash = self.client.get(reverse('dashboard'))
        self.assertEqual(res_dash.status_code, 200)
        self.assertContains(res_dash, self.user.avatar_url)

        res_home = self.client.get(reverse('home'))
        self.assertEqual(res_home.status_code, 200)
        self.assertContains(res_home, self.user.avatar_url)

        res_projects = self.client.get(reverse('projects_list'))
        self.assertEqual(res_projects.status_code, 200)
        self.assertContains(res_projects, self.user.avatar_url)

    # ------------------------------------------------------------------------
    # ۸. آزمون‌های صفحه جزئیات پروژه و ثبت پیشنهاد (/projects/<id>/)
    # ------------------------------------------------------------------------
    def test_project_detail_view_and_proposal_submission(self):
        """مشاهده صفحه جزئیات پروژه و ثبت پیشنهاد قیمت توسط فریلنسر مطابق تصاویر ۲۳، ۲۴ و ۲۵"""
        from accounts.models import Project, Proposal, Skill, ProjectSkill

        # ایجاد کارفرمای نمونه
        employer = User.objects.create_user(
            email='employer_test@example.com',
            password='Password123',
            first_name='علی',
            last_name='طاهری',
            username='alitaheri',
            role='EMPLOYER'
        )

        project = Project.objects.create(
            employer=employer,
            title='توسعه اپلیکیشن IoT با ESP32',
            description='توضیحات کامل پروژه سخت‌افزاری و نرم‌افزاری',
            pricing_type='FIXED_PRICE',
            budget=25000000,
            status='OPEN'
        )

        skill, _ = Skill.objects.get_or_create(name='C++')
        ProjectSkill.objects.create(project=project, skill=skill, is_required=True)

        # ۱. مشاهده جزئیات پروژه (مهمان یا کاربر لاگین‌شده)
        detail_url = reverse('project_detail', args=[project.id])
        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'توسعه اپلیکیشن IoT با ESP32')
        self.assertContains(res, '25000000 تومان')
        self.assertContains(res, 'C++')
        self.assertContains(res, 'ارسال پیشنهاد')

        # ۲. ارسال پیشنهاد موفق توسط فریلنسر
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)
        res_post = self.client.post(detail_url, {
            'bid_amount': '22000000',
            'estimated_duration': '14',
            'cover_letter': 'پیشنهاد با بهترین کیفیت و سابقه پیاده‌سازی پروژه‌های مشابه'
        }, follow=True)
        self.assertEqual(res_post.status_code, 200)
        self.assertContains(res_post, 'پیشنهاد شما با موفقیت برای این پروژه ثبت شد')

        # ۳. بررسی ذخیره شدن در دیتابیس
        prop = Proposal.objects.get(project=project, freelancer=self.user)
        self.assertEqual(float(prop.bid_amount), 22000000.0)
        self.assertEqual(prop.estimated_duration, 14)
        self.assertEqual(prop.status, 'PENDING')

        # ۴. جلوگیری از ارسال پیشنهاد مجدد برای همان پروژه (Duplicate prevention)
        res_dup = self.client.post(detail_url, {
            'bid_amount': '20000000',
            'estimated_duration': '10',
            'cover_letter': 'تلاش مجدد'
        }, follow=True)
        self.assertEqual(res_dup.status_code, 200)
        self.assertContains(res_dup, 'شما قبلاً برای این پروژه پیشنهاد ارسال کرده‌اید')

        # ۵. کارفرما نمی‌تواند برای پروژه خودش پیشنهاد ثبت کند
        self.client.login(email='employer_test@example.com', password='Password123')
        res_emp = self.client.post(detail_url, {
            'bid_amount': '15000000',
            'estimated_duration': '5',
            'cover_letter': 'پیشنهاد کارفرما'
        }, follow=True)
        self.assertEqual(res_emp.status_code, 200)
        self.assertContains(res_emp, 'کارفرما نمی‌تواند برای پروژه‌ای که خودش ثبت کرده پیشنهاد ثبت کند')

    # ------------------------------------------------------------------------
    # ۹. آزمون‌های صفحه دسته‌بندی‌ها و مهارت‌ها (/categories/)
    # ------------------------------------------------------------------------
    def test_categories_view_accessible_and_contents(self):
        """مشاهده صفحه دسته‌بندی‌ها و مهارت‌ها مطابق با تصویر ۲۸ پونیشا"""
        res = self.client.get(reverse('categories'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'دسته‌بندی‌ها')
        self.assertContains(res, 'طراحی و خلاقیت')
        self.assertContains(res, 'توسعه نرم‌افزار و آی‌تی')
        self.assertContains(res, 'بازاریابی و فروش')
        self.assertContains(res, 'محتوا و ترجمه')
        self.assertContains(res, 'مالی و کسب‌وکار')
        self.assertContains(res, 'مهندسی و معماری')
        self.assertContains(res, 'طراحی سایت')
        self.assertContains(res, 'طراحی گرافیک')

    # ------------------------------------------------------------------------
    # ۱۰. آزمون‌های صفحه فهرست فریلنسرها و دعوت به همکاری (/freelancers/)
    # ------------------------------------------------------------------------
    def test_freelancers_list_view_and_invitation(self):
        """مشاهده بانک فریلنسرها، نمایش پویا پس از ثبت‌نام، مهارت‌ها و ارسال دعوت‌نامه"""
        from accounts.models import Skill, UserSkill, UserProfile

        # ایجاد فریلنسر نمونه جدید برای اطمینان از پویایی اضافه شدن فریلنسرها
        new_freelancer = User.objects.create_user(
            email='new_freelancer_test@example.com',
            password='Password123',
            first_name='سامان',
            last_name='کریمی',
            username='samankarimi',
            role='FREELANCER'
        )
        UserProfile.objects.create(
            user=new_freelancer,
            professional_title='توسعه‌دهنده فلاتر و اندروید',
            location='مشهد، ایران',
            bio='طراحی اپلیکیشن‌های موبایل کراس‌پلتفرم با فلاتر'
        )
        flutter_skill, _ = Skill.objects.get_or_create(name='Flutter')
        UserSkill.objects.create(user=new_freelancer, skill=flutter_skill)

        # ۱. دسترسی به صفحه فریلنسرها و مشاهده فریلنسر جدید همراه با مهارت‌ها
        res = self.client.get(reverse('freelancers_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'سامان کریمی')
        self.assertContains(res, '@samankarimi')
        self.assertContains(res, 'توسعه‌دهنده فلاتر و اندروید')
        self.assertContains(res, 'Flutter')
        self.assertContains(res, 'دعوت به همکاری')

        # ۲. جستجوی فریلنسر بر اساس مهارت
        res_search = self.client.get(reverse('freelancers_list') + '?q=Flutter')
        self.assertEqual(res_search.status_code, 200)
        self.assertContains(res_search, 'سامان کریمی')

        # ۳. ارسال دعوت‌نامه همکاری توسط کارفرما
        employer = User.objects.create_user(
            email='employer_inviter@example.com',
            password='Password123',
            first_name='حامد',
            last_name='احمدی',
            username='hamed_employer',
            role='EMPLOYER'
        )
        self.client.login(email='employer_inviter@example.com', password='Password123')
        res_invite = self.client.post(reverse('freelancers_list'), {
            'freelancer_id': new_freelancer.id,
            'message': 'دعوت به پروژه موبایل'
        }, follow=True)
        self.assertEqual(res_invite.status_code, 200)
        self.assertContains(res_invite, 'دعوت‌نامه همکاری با موفقیت برای')

    # ------------------------------------------------------------------------
    # ۱۱. آزمون‌های بخش اطلاعیه‌ها و پیام‌های داشبورد (تصاویر ۲۹ و ۳۰)
    # ------------------------------------------------------------------------
    def test_dashboard_announcements_and_messages_sections(self):
        """مشاهده بخش‌های اطلاعیه‌های من و پیام‌های من در داشبورد مطابق تصاویر ۲۹ و ۳۰ پونیشا"""
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)

        # ۱. بخش اطلاعیه‌ها (?section=announcements)
        res_ann = self.client.get(reverse('dashboard') + '?section=announcements')
        self.assertEqual(res_ann.status_code, 200)
        self.assertContains(res_ann, 'اطلاعیه‌های من')
        self.assertContains(res_ann, 'خوش آمدید')
        self.assertContains(res_ann, '۲۳ آبان ۱۴۰۵')
        self.assertContains(res_ann, 'تنظیم مهارت‌ها:')

        # ۲. بخش پیام‌ها (?section=messages)
        res_msg = self.client.get(reverse('dashboard') + '?section=messages')
        self.assertEqual(res_msg.status_code, 200)
        self.assertContains(res_msg, 'پیام های من')
        self.assertContains(res_msg, 'پیام‌های پشتیبانی')
        self.assertContains(res_msg, 'شما هنوز مکالمه ای رو شروع نکردید')
        self.assertContains(res_msg, 'برای شروع به گفت‌وگو لطفا یکی از مکالمه ها را انتخاب کنید')

        # ۳. تست ریدایرکت‌های کمکی
        res_notif_redir = self.client.get(reverse('dashboard_notifications'))
        self.assertEqual(res_notif_redir.status_code, 302)
        self.assertIn('section=announcements', res_notif_redir.headers.get('Location'))

        res_msg_redir = self.client.get(reverse('dashboard_messages'))
        self.assertEqual(res_msg_redir.status_code, 302)
        self.assertIn('section=messages', res_msg_redir.headers.get('Location'))

        # ۴. تست وجود لینک‌های اطلاعیه‌ها و پیام‌ها در سایدبار کشویی (user_drawer.html)
        res_home = self.client.get(reverse('home'))
        self.assertEqual(res_home.status_code, 200)
        self.assertContains(res_home, 'section=announcements')
        self.assertContains(res_home, 'section=messages')

        # ۵. بخش کلینیک پروفایل (?section=clinic) و حذف کامل گزینه پروفایل برجسته (تصویر ۳۲)
        res_clinic = self.client.get(reverse('dashboard') + '?section=clinic')
        self.assertEqual(res_clinic.status_code, 200)
        self.assertContains(res_clinic, 'کلینیک پروفایل')
        self.assertContains(res_clinic, 'اولین بررسی پروفایل خود را شروع کنید')
        self.assertContains(res_clinic, 'بررسی‌های قبلی پروفایل')
        self.assertContains(res_clinic, 'هنوز بررسی قبلی برای نمایش وجود ندارد')
        self.assertNotContains(res_clinic, 'پروفایل برجسته')
        self.assertNotContains(res_home, 'پروفایل برجسته')

        # ۶. دراور کشویی پیام‌ها و پشتیبانی در تمام صفحات (تصاویر ۳۳ و ۳۴)
        self.assertContains(res_home, 'messages-drawer')
        self.assertContains(res_home, 'پیام‌های پشتیبانی')
        self.assertContains(res_home, 'تیکتی یافت نشد، برای شروع میتوانید تیکتی ارسال کنید')
        self.assertContains(res_home, 'تیکت جدید')
        self.assertContains(res_home, 'شما هنوز مکالمه ای رو شروع نکردید')
        self.assertContains(res_home, 'toggleMessagesDrawer')

    # ------------------------------------------------------------------------
    # ۱۲. آزمون‌های صفحه ثبت سریع پروژه (تصویر ۴۶) و جایگزینی دکمه هدر
    # ------------------------------------------------------------------------
    def test_project_create_view_and_header_button(self):
        """مشاهده صفحه ایجاد پروژه جدید (مرحله ۱: انتخاب روش ثبت) و جایگزینی دکمه هدر"""
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)

        # ۱. بررسی هدر صفحه اصلی (دکمه ثبت سریع پروژه جایگزین داشبورد من شده است)
        res_home = self.client.get(reverse('home'))
        self.assertEqual(res_home.status_code, 200)
        self.assertContains(res_home, 'ثبت سریع پروژه')
        self.assertNotContains(res_home, 'داشبورد من')

        # ۲. دسترسی به صفحه ثبت پروژه جدید (/projects/new/)
        res_create = self.client.get(reverse('project_create'))
        self.assertEqual(res_create.status_code, 200)
        self.assertContains(res_create, 'ثبت پروژه جدید')
        self.assertNotContains(res_create, 'در همین تب مرورگر')
        self.assertContains(res_create, 'روش ثبت پروژه را انتخاب کنید')
        self.assertContains(res_create, 'ثبت پروژه به‌صورت دستی')
        self.assertContains(res_create, 'با دستیار هوشمند')
        self.assertContains(res_create, 'ادامه به فرم ثبت دستی')

        # ۳. دسترسی به مرحله ۲ ثبت پروژه با فرم کامل تنظیمات (تصاویر ۵۱ تا ۵۶)
        res_step2 = self.client.get(reverse('project_create') + '?step=2')
        self.assertEqual(res_step2.status_code, 200)
        self.assertContains(res_step2, 'تنظیمات پروژه')
        self.assertContains(res_step2, 'فرم ثبت دستی فعال است')
        self.assertContains(res_step2, 'شرح پروژه')
        self.assertContains(res_step2, 'فایل‌های پروژه')
        self.assertContains(res_step2, 'اولویت و بودجه')
        self.assertContains(res_step2, 'ادامه و انتشار پروژه')

        # ۴. ارسال فرم مرحله ۲ و انتشار مستقیم پروژه
        res_publish = self.client.post(reverse('project_create'), {
            'title': 'طراحی پلتفرم کتابداری آنلاین',
            'description': 'هدف این پروژه، طراحی و پیاده‌سازی سامانه تحت وب کتابداری با امکان دسته‌بندی و مدیریت امانت است.',
            'category_id': 1,
            'skills': ['برنامه نویسی', 'تست نرم افزار', 'Database Programming'],
            'budget_min': '15000000',
            'budget_max': '30000000',
            'pricing_type': 'FIXED_PRICE',
            'submit_action': 'publish'
        }, follow=True)
        self.assertEqual(res_publish.status_code, 200)
        self.assertContains(res_publish, 'پروژه جدید شما با موفقیت ثبت')

        # بررسی در دیتابیس
        from accounts.models import Project
        p = Project.objects.filter(title='طراحی پلتفرم کتابداری آنلاین').first()
        self.assertIsNotNone(p)
        self.assertEqual(p.status, 'OPEN')
        self.assertEqual(float(p.budget), 30000000.0)

        # ۵. ذخیره پروژه به صورت پیش‌نویس (Draft)
        res_draft = self.client.post(reverse('project_create'), {
            'title': 'طراحی آزمایشی در حالت پیش‌نویس',
            'description': 'این یک پروژه تستی پیش‌نویس است.',
            'category_id': 1,
            'budget_min': '10000000',
            'budget_max': '20000000',
            'pricing_type': 'FIXED_PRICE',
            'submit_action': 'draft'
        }, follow=True)
        self.assertEqual(res_draft.status_code, 200)
        self.assertContains(res_draft, 'پروژه شما با موفقیت به عنوان پیش‌نویس (Draft) ذخیره شد')

        p_draft = Project.objects.filter(title='طراحی آزمایشی در حالت پیش‌نویس').first()
        self.assertIsNotNone(p_draft)
        self.assertEqual(p_draft.status, 'DRAFT')

    # ------------------------------------------------------------------------
    # ۱۳. آزمون‌های تغییر نقش کاربری و تطبیق سایدبار کشویی (تصاویر ۴۸، ۴۹ و ۵۰)
    # ------------------------------------------------------------------------
    def test_switch_role_endpoint_and_drawer(self):
        """تغییر نقش کاربر بین فریلنسر و کارفرما و نمایش اعلان تایید"""
        self.client.login(email='mahtabmj96@gmail.com', password=self.user_password)

        # ۱. تغییر نقش به کارفرما
        res_to_emp = self.client.post(reverse('switch_role'), {'role': 'EMPLOYER'})
        self.assertEqual(res_to_emp.status_code, 200)
        self.assertEqual(res_to_emp.json().get('status'), 'ok')
        self.assertEqual(res_to_emp.json().get('role'), 'EMPLOYER')

        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'EMPLOYER')

        # ۲. تغییر نقش مجدد به فریلنسر
        res_to_fl = self.client.post(reverse('switch_role'), {'role': 'FREELANCER'})
        self.assertEqual(res_to_fl.status_code, 200)
        self.assertEqual(res_to_fl.json().get('role'), 'FREELANCER')

        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'FREELANCER')


