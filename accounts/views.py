from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.db.models import Q

from .models import User, Category, Skill, UserSkill, Project, Proposal, UserProfile, Portfolio, Certificate
from .forms import LoginForm, SignupForm, ForgotPasswordForm, ResetPasswordForm, RoleSelectionForm
from .rate_limit import (
    is_login_rate_limited,
    record_login_failed_attempt,
    reset_login_attempts,
    check_forgot_password_rate_limit,
)


def home_view(request):
    """صفحه اصلی و لندینگ پیج پلتفرم فریلنسری (Home Page)"""
    latest_projects = Project.objects.filter(status='OPEN').order_by('-created_at')[:8]

    initials = "MA"
    if request.user.is_authenticated and request.user.first_name and request.user.last_name:
        initials = (request.user.first_name[0] + request.user.last_name[0]).upper()

    return render(request, 'accounts/home.html', {
        'latest_projects': latest_projects,
        'user_initials': initials,
    })


def login_view(request):
    """صفحه ورود با پشتیبانی از قابلیت 'مرا به خاطر بسپار'، هدایت به صفحه اصلی و محدودیت نرخ درخواست"""
    if request.user.is_authenticated:
        return redirect('home')

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

            if not user.username or not user.role:
                response = redirect('select_role')
            else:
                response = redirect('home')  # هدایت مستقیم به صفحه اصلی طبق درخواست کاربر

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
                return redirect('onboarding_categories')
            else:
                return redirect('home')
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
    """مرحله ۲ از ۲: انتخاب مهارت‌های تخصصی با بازگشت به صفحه مبدا (پروفایل یا داشبورد)"""
    skills = Skill.objects.all().order_by('name')
    user = request.user

    # دریافت صفحه مبدا (next) برای بازگشت به همان صفحه قبلی کاربر
    next_url = request.POST.get('next') or request.GET.get('next')
    if not next_url:
        referer = request.META.get('HTTP_REFERER', '')
        if referer and 'onboarding' not in referer and 'login' not in referer:
            next_url = referer

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

            # بازگشت به صفحه قبلی کاربر (پروفایل یا داشبورد) یا صفحه اصلی
            if next_url:
                return redirect(next_url)
            return redirect('home')

    user_skills_ids = list(UserSkill.objects.filter(user=user).values_list('skill_id', flat=True))
    return render(request, 'accounts/onboarding_skills.html', {
        'skills': skills,
        'user_skills_ids': user_skills_ids,
        'next_url': next_url,
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

    profile, _ = UserProfile.objects.get_or_create(user=user)

    # محاسبه اینیشیال آواتار (مانند MA در پونیشا)
    initials = user.initials

    # محاسبه درصد تکمیل پروفایل (همگام با صفحه پروفایل)
    profile_percent = 30
    if user.username:
        profile_percent += 15
    if profile.bio:
        profile_percent += 15
    if profile.location:
        profile_percent += 10
    if user_skills.exists():
        profile_percent += 15
    if profile.avatar:
        profile_percent += 15

    return render(request, 'accounts/dashboard.html', {
        'user': user,
        'profile': profile,
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
def profile_view(request):
    """صفحه پروفایل کاربر مطابق اسکرین‌شات پونیشا با قابلیت ثبت درباره من و نمونه‌کارها"""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    user_skills = UserSkill.objects.filter(user=user).select_related('skill')
    portfolios = Portfolio.objects.filter(user=user).order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_bio':
            bio_text = request.POST.get('bio', '').strip()
            profile.bio = bio_text
            profile.save()
            messages.success(request, 'بخش درباره من با موفقیت به‌روزرسانی شد.')
        elif action == 'update_location':
            loc = request.POST.get('location', '').strip()
            profile.location = loc
            profile.save()
            messages.success(request, 'موقعیت مکانی شما با موفقیت ذخیره شد.')
        elif action == 'add_portfolio':
            title = request.POST.get('portfolio_title', '').strip()
            desc = request.POST.get('portfolio_desc', '').strip()
            url = request.POST.get('portfolio_url', '').strip()
            if title:
                Portfolio.objects.create(user=user, title=title, description=desc, project_url=url)
                messages.success(request, 'نمونه‌کار جدید با موفقیت اضافه شد.')
        elif action == 'upload_avatar':
            avatar_file = request.FILES.get('avatar_file')
            if not avatar_file:
                messages.error(request, 'لطفاً یک فایل تصویر برای پروفایل انتخاب کنید.')
            elif avatar_file.size > 5 * 1024 * 1024:
                messages.error(request, 'حجم فایل بیشتر از ۵ مگابایت است. لطفاً فایل کم‌حجم‌تری انتخاب نمایید.')
            else:
                import os
                ext = os.path.splitext(avatar_file.name)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                    messages.error(request, 'فرمت فایل معتبر نیست؛ فقط فایل‌های تصویری با فرمت jpeg، jpg، png و webp مجاز هستند.')
                else:
                    profile.avatar = avatar_file
                    profile.save()
                    messages.success(request, 'تصویر پروفایل شما با موفقیت ذخیره شد!')
        return redirect('profile')

    initials = "MA"
    if user.first_name and user.last_name:
        initials = (user.first_name[0] + user.last_name[0]).upper()

    profile_percent = 30
    if user.username:
        profile_percent += 15
    if profile.bio:
        profile_percent += 15
    if profile.location:
        profile_percent += 10
    if user_skills.exists():
        profile_percent += 15
    if profile.avatar:
        profile_percent += 15

    return render(request, 'accounts/profile.html', {
        'user': user,
        'profile': profile,
        'user_skills': user_skills,
        'portfolios': portfolios,
        'user_initials': initials,
        'profile_percent': min(profile_percent, 100),
    })


@login_required
def welcome_view(request):
    """ریدایرکت به داشبورد اصلی"""
    return redirect('dashboard')


def projects_list_view(request):
    """صفحه لیست تمام پروژه‌های باز با نوار افقی فیلتر و قابلیت جستجو"""
    projects = Project.objects.filter(status='OPEN').select_related('employer').prefetch_related('projectskill_set__skill', 'projectcategory_set__category').order_by('-created_at')

    # ۱. جستجو در عنوان و توضیحات پروژه
    query = request.GET.get('q', '').strip()
    if query:
        projects = projects.filter(Q(title__icontains=query) | Q(description__icontains=query))

    # ۲. فیلتر دسته‌بندی
    category_id = request.GET.get('category', '').strip()
    if category_id and category_id.isdigit():
        projects = projects.filter(projectcategory__category_id=int(category_id))

    # ۳. فیلتر نوع قیمت‌گذاری (ثابت یا ساعتی)
    pricing_type = request.GET.get('pricing_type', '').strip()
    if pricing_type in ['FIXED_PRICE', 'HOURLY']:
        projects = projects.filter(pricing_type=pricing_type)

    categories = Category.objects.all().order_by('id')

    initials = "MA"
    if request.user.is_authenticated and request.user.first_name and request.user.last_name:
        initials = (request.user.first_name[0] + request.user.last_name[0]).upper()

    return render(request, 'accounts/projects_list.html', {
        'projects': projects,
        'categories': categories,
        'query': query,
        'selected_category': int(category_id) if category_id and category_id.isdigit() else None,
        'selected_pricing_type': pricing_type,
        'total_count': projects.count(),
        'user_initials': initials,
    })


def project_detail_view(request, project_id):
    """صفحه جزئیات پروژه و ثبت پیشنهاد (Proposal) مطابق تصاویر ۲۳، ۲۴ و ۲۵ پونیشا"""
    project = get_object_or_404(
        Project.objects.select_related('employer').prefetch_related('projectskill_set__skill', 'projectcategory_set__category'),
        pk=project_id
    )

    project_skills = project.projectskill_set.all()
    project_categories = project.projectcategory_set.all()
    proposals = project.proposals.select_related('freelancer').order_by('-created_at')

    user = request.user
    user_proposal = None
    if user.is_authenticated:
        user_proposal = proposals.filter(freelancer=user).first()

    if request.method == 'POST':
        if not user.is_authenticated:
            messages.error(request, 'برای ارسال پیشنهاد، ابتدا باید وارد حساب کاربری خود شوید.')
            return redirect('login')

        if project.employer_id == user.id:
            messages.error(request, 'کارفرما نمی‌تواند برای پروژه‌ای که خودش ثبت کرده پیشنهاد ثبت کند.')
            return redirect('project_detail', project_id=project.id)

        if user_proposal:
            messages.warning(request, 'شما قبلاً برای این پروژه پیشنهاد ارسال کرده‌اید.')
            return redirect('project_detail', project_id=project.id)

        bid_amount_str = request.POST.get('bid_amount', '').strip().replace(',', '')
        estimated_duration = request.POST.get('estimated_duration', '').strip()
        cover_letter = request.POST.get('cover_letter', '').strip()

        if not bid_amount_str:
            messages.error(request, 'لطفاً مبلغ پیشنهادی خود را وارد کنید.')
            return redirect('project_detail', project_id=project.id)

        try:
            bid_amount = float(bid_amount_str)
            if bid_amount <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, 'مبلغ پیشنهادی باید یک عدد معتبر و بزرگتر از صفر باشد.')
            return redirect('project_detail', project_id=project.id)

        duration = None
        if estimated_duration and estimated_duration.isdigit():
            duration = int(estimated_duration)

        if not cover_letter:
            cover_letter = 'پیشنهاد انجام پروژه مطابق با الزامات کارفرما با بهترین کیفیت و در موعد مقرر.'

        Proposal.objects.create(
            project=project,
            freelancer=user,
            bid_amount=bid_amount,
            estimated_duration=duration,
            cover_letter=cover_letter,
            status='PENDING'
        )

        messages.success(request, 'پیشنهاد شما با موفقیت برای این پروژه ثبت شد!')
        return redirect('project_detail', project_id=project.id)

    initials = "MA"
    if user.is_authenticated and user.first_name and user.last_name:
        initials = (user.first_name[0] + user.last_name[0]).upper()

    return render(request, 'accounts/project_detail.html', {
        'project': project,
        'project_skills': project_skills,
        'project_categories': project_categories,
        'proposals': proposals,
        'proposals_count': proposals.count(),
        'user_proposal': user_proposal,
        'user_initials': initials,
    })


def categories_view(request):
    """صفحه لیست دسته‌بندی‌ها و مهارت‌ها مطابق با تصویر ۲۸ پونیشا (ponisha.ir/categories)"""
    categories_data = [
        {
            'name': 'طراحی و خلاقیت',
            'icon': '✒️',
            'skills': [
                'طراحی گرافیک',
                'تصویرسازی',
                'طراحی بنر و بیلبورد',
                'طراحی کاتالوگ و بروشور',
                'طراحی رابط کاربری UI/UX',
                'تولید و ویرایش ویدیو',
                'عکاسی و ادیت تصویر',
                'طراحی پست و استوری',
            ]
        },
        {
            'name': 'توسعه نرم‌افزار و آی‌تی',
            'icon': '💻',
            'skills': [
                'طراحی سایت',
                'طراحی اپلیکیشن موبایل',
                'اسکریپت‌نویسی و اتوماسیون',
                'برنامه‌نویسی و توسعه نرم‌افزار',
                'طراحی فروشگاه آنلاین',
                'طراحی قالب وردپرس',
                'توسعه وب، سرور و امنیت',
                'طراحی و توسعه بازی',
            ]
        },
        {
            'name': 'بازاریابی و فروش',
            'icon': '🎯',
            'skills': [
                'سئو SEO',
                'تبلیغات اینترنتی',
                'دیجیتال مارکتینگ',
                'پشتیبانی مشتریان',
                'تحقیقات بازار و استراتژی',
                'ادمین اینستاگرام و شبکه‌ها',
                'ورود اطلاعات در وبسایت',
                'استخراج داده و جستجو',
            ]
        },
        {
            'name': 'محتوا و ترجمه',
            'icon': '📄',
            'skills': [
                'ترجمه تخصصی',
                'پژوهش و مقاله‌نویسی',
                'تایپ و رونویسی',
                'ویراستاری و نگارش',
                'تولید محتوا برای سایت',
                'کپی‌رایتینگ و نگارش تبلیغاتی',
            ]
        },
        {
            'name': 'مالی و کسب‌وکار',
            'icon': '💼',
            'skills': [
                'تجزیه و تحلیل کسب‌وکار',
                'طرح کسب‌وکار و مدل مالی',
                'حسابداری و امور مالی',
                'مشاوره استارتاپ و رشد',
                'مشاوره حقوقی و قراردادها',
                'مدیریت پروژه و برنامه‌ریزی',
            ]
        },
        {
            'name': 'مهندسی و معماری',
            'icon': '🏛️',
            'skills': [
                'طراحی معماری و دکوراسیون',
                'مدل‌سازی سه‌بعدی و رندر',
                'نقشه‌کشی اتوکد صنعتی',
                'مهندسی برق و الکترونیک',
                'شبیه‌سازی و مهندسی مکانیک',
                'برنامه‌نویسی سخت‌افزار و اینترنت اشیاء',
            ]
        },
    ]

    initials = "MA"
    if request.user.is_authenticated and request.user.first_name and request.user.last_name:
        initials = (request.user.first_name[0] + request.user.last_name[0]).upper()

    return render(request, 'accounts/categories.html', {
        'categories_data': categories_data,
        'user_initials': initials,
    })


def freelancers_list_view(request):
    """صفحه لیست تمام فریلنسرهای فعال در دیتابیس با امکان جستجو، مشاهده مهارت‌ها و دعوت به همکاری"""
    freelancers = User.objects.filter(role='FREELANCER').select_related('userprofile').prefetch_related('userskill_set__skill').order_by('-id')

    # جستجو بر اساس نام، نام کاربری، عنوان شغلی، بیوگرافی یا نام مهارت
    query = request.GET.get('q', '').strip()
    if query:
        freelancers = freelancers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(userprofile__professional_title__icontains=query) |
            Q(userprofile__bio__icontains=query) |
            Q(userskill__skill__name__icontains=query)
        ).distinct()

    # مدیریت ارسال دعوت‌نامه همکاری
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'برای ارسال دعوت‌نامه همکاری، ابتدا وارد حساب کاربری خود شوید.')
            return redirect('login')

        freelancer_id = request.POST.get('freelancer_id')
        target_freelancer = get_object_or_404(User, pk=freelancer_id, role='FREELANCER')

        if request.user.id == target_freelancer.id:
            messages.warning(request, 'شما نمی‌توانید برای خودتان دعوت‌نامه همکاری ارسال کنید.')
        else:
            messages.success(request, f'دعوت‌نامه همکاری با موفقیت برای {target_freelancer.full_name or target_freelancer.username} ارسال شد!')

        return redirect('freelancers_list')

    # پروژه‌های باز کارفرما برای انتخاب در مودال دعوت به همکاری
    employer_projects = []
    if request.user.is_authenticated:
        employer_projects = Project.objects.filter(employer=request.user, status='OPEN')

    initials = "MA"
    if request.user.is_authenticated and request.user.first_name and request.user.last_name:
        initials = (request.user.first_name[0] + request.user.last_name[0]).upper()

    return render(request, 'accounts/freelancers_list.html', {
        'freelancers': freelancers,
        'query': query,
        'total_count': freelancers.count(),
        'employer_projects': employer_projects,
        'user_initials': initials,
    })


def terms_view(request):
    """صفحه قوانین و مقررات پلتفرم فریلنسری مطابق استاندارد پونیشا"""
    initials = "MA"
    if request.user.is_authenticated and request.user.first_name and request.user.last_name:
        initials = (request.user.first_name[0] + request.user.last_name[0]).upper()

    return render(request, 'accounts/terms.html', {
        'user_initials': initials,
    })


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
