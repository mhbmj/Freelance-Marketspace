from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


# ============================================================================
# ۱. مدل کاربر (Users)
# ============================================================================
class UserManager(BaseUserManager):
    """مدیریت ایجاد کاربران با ایمیل به عنوان شناسه اصلی"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('ایمیل الزامی است.')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)  # هش امن با الگوریتم PBKDF2
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        Admin.objects.get_or_create(user=user, role_title='Super Administrator')
        return user


class User(AbstractBaseUser):
    """جدول کاربران - منطبق بر جدول users در پایگاه داده PostgreSQL"""

    first_name = models.CharField('نام', max_length=50)
    last_name = models.CharField('نام خانوادگی', max_length=50)
    email = models.EmailField('ایمیل', max_length=100, unique=True)
    username = models.CharField('نام کاربری', max_length=50, unique=True, null=True, blank=True)
    phone_number = models.CharField('شماره موبایل', max_length=20, blank=True, null=True)

    ROLE_CHOICES = [
        ('FREELANCER', 'فریلنسر هستم'),
        ('EMPLOYER', 'کارفرما هستم'),
    ]
    role = models.CharField('نقش کاربر', max_length=20, choices=ROLE_CHOICES, default='FREELANCER', null=True, blank=True)

    # اتصال فیلد password جنگو به ستون password_hash در جدول users
    password = models.CharField('رمز عبور هش‌شده', max_length=255, db_column='password_hash')

    STATUS_CHOICES = [
        ('ACTIVE', 'فعال'),
        ('INACTIVE', 'غیرفعال'),
        ('SUSPENDED', 'مسدود'),
    ]
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    created_at = models.DateTimeField('تاریخ ثبت‌نام', auto_now_add=True)
    updated_at = models.DateTimeField('آخرین ویرایش', auto_now=True)
    last_login = models.DateTimeField('آخرین ورود', blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        db_table = 'users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def initials(self):
        """محاسبه حروف اختصاری نام برای نمایش به عنوان آواتار پیش‌فرض"""
        if self.first_name and self.last_name:
            return (self.first_name[0] + self.last_name[0]).upper()
        if self.first_name:
            return self.first_name[:2].upper()
        if self.username:
            return self.username[:2].upper()
        return "MA"

    @property
    def avatar_url(self):
        """آدرس تصویر آواتار آپلود شده در صورت وجود در جدول user_profiles"""
        try:
            profile = getattr(self, 'userprofile', None)
            if profile and profile.avatar:
                return profile.avatar.url
        except Exception:
            return None
        return None

    @property
    def is_active(self):
        return self.status == 'ACTIVE'

    @property
    def is_staff(self):
        return Admin.objects.filter(user=self).exists()

    @property
    def is_superuser(self):
        return self.is_staff

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff


# ============================================================================
# ۲. مدل مدیران (Admins)
# ============================================================================
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, db_column='user_id')
    role_title = models.CharField('عنوان نقش', max_length=50, default='Admin')
    granted_at = models.DateTimeField('تاریخ اعطا', auto_now_add=True)

    class Meta:
        verbose_name = 'مدیر سیستم'
        verbose_name_plural = 'مدیران سیستم'
        db_table = 'admins'

    def __str__(self):
        return f"Admin: {self.user.email} ({self.role_title})"


# ============================================================================
# ۳. مدل پروفایل کاربر (User Profiles)
# ============================================================================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, db_column='user_id')
    avatar = models.FileField('تصویر پروفایل', upload_to='avatars/', blank=True, null=True)
    professional_title = models.CharField('عنوان حرفه‌ای', max_length=100, blank=True, null=True)
    bio = models.TextField('معرفی / بیوگرافی', blank=True, null=True)
    location = models.CharField('موقعیت مکانی', max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile: {self.user.email}"


# ============================================================================
# ۴. نمونه‌کارها (Portfolios)
# ============================================================================
class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    title = models.CharField('عنوان نمونه‌کار', max_length=150)
    service_type = models.CharField('نوع سرویس', max_length=100, blank=True, null=True)
    user_role = models.CharField('نقش شما در پروژه', max_length=100, blank=True, null=True)
    description = models.TextField('توضیحات', blank=True, null=True)
    skills = models.CharField('مهارت‌ها', max_length=255, blank=True, null=True)
    tags = models.CharField('برچسب‌ها', max_length=255, blank=True, null=True)
    duration = models.CharField('مدت زمان انجام', max_length=50, blank=True, null=True)
    min_price = models.DecimalField('حداقل قیمت', max_digits=12, decimal_places=0, blank=True, null=True)
    max_price = models.DecimalField('حداکثر قیمت', max_digits=12, decimal_places=0, blank=True, null=True)
    file = models.FileField('فایل نمونه‌کار', upload_to='portfolios/', blank=True, null=True)
    project_url = models.URLField('لینک پروژه', max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'نمونه‌کار'
        verbose_name_plural = 'نمونه‌کارها'
        db_table = 'portfolios'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ============================================================================
# ۵. گواهینامه‌ها (Certificates)
# ============================================================================
class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    title = models.CharField('عنوان مدرک', max_length=150)
    issuing_organization = models.CharField('سازمان صادرکننده', max_length=150)
    issue_date = models.DateField('تاریخ صدور')
    credential_url = models.URLField('لینک مدرک', max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'گواهینامه'
        verbose_name_plural = 'گواهینامه‌ها'
        db_table = 'certificates'

    def __str__(self):
        return self.title


class WorkExperience(models.Model):
    """مدل سوابق کاری کاربر مطابق تصویر ۳۹ پونیشا"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_experiences')
    title = models.CharField('سمت / عنوان شغلی', max_length=150)
    company = models.CharField('شرکت / مجموعه', max_length=150)
    start_date = models.CharField('از تاریخ', max_length=50, blank=True, null=True)
    end_date = models.CharField('تا تاریخ', max_length=50, blank=True, null=True)
    is_current = models.BooleanField('تا امروز', default=False)
    description = models.TextField('توضیحات', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سابقه کاری'
        verbose_name_plural = 'سوابق کاری'
        db_table = 'work_experiences'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} در {self.company}"


class Education(models.Model):
    """مدل سوابق تحصیلی کاربر مطابق تصویر ۴۰ پونیشا"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='educations')
    degree = models.CharField('مدرک / رشته تحصیلی', max_length=150)
    institution = models.CharField('نام آموزشگاه / دانشگاه', max_length=150)
    start_date = models.CharField('از تاریخ', max_length=50, blank=True, null=True)
    end_date = models.CharField('تا تاریخ', max_length=50, blank=True, null=True)
    is_current = models.BooleanField('تا امروز', default=False)
    description = models.TextField('توضیحات', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سابقه تحصیلی'
        verbose_name_plural = 'سوابق تحصیلی'
        db_table = 'educations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.degree} در {self.institution}"


# ============================================================================
# ۶. دسته‌بندی‌ها (Categories)
# ============================================================================
class Category(models.Model):
    name = models.CharField('نام دسته‌بندی', max_length=50)
    description = models.TextField('توضیحات', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        db_table = 'categories'

    def __str__(self):
        return self.name


# ============================================================================
# ۷. مهارت‌ها (Skills)
# ============================================================================
class Skill(models.Model):
    name = models.CharField('نام مهارت', max_length=50)
    description = models.TextField('توضیحات', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مهارت'
        verbose_name_plural = 'مهارت‌ها'
        db_table = 'skills'

    def __str__(self):
        return self.name


# ============================================================================
# ۸. جدول واسط مهارت‌های کاربر (User Skills)
# ============================================================================
class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    years_of_experience = models.IntegerField('سابقه کار (سال)', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مهارت کاربر'
        verbose_name_plural = 'مهارت‌های کاربران'
        db_table = 'user_skills'
        unique_together = ('user', 'skill')


# ============================================================================
# ۹. پروژه‌ها (Projects)
# ============================================================================
class Project(models.Model):
    PRICING_TYPES = [
        ('FIXED_PRICE', 'قیمت ثابت'),
        ('HOURLY', 'ساعتی'),
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'پیش‌نویس'),
        ('OPEN', 'باز'),
        ('IN_PROGRESS', 'در حال انجام'),
        ('COMPLETED', 'تکمیل‌شده'),
        ('CANCELLED', 'لغو‌شده'),
    ]

    employer = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='projects_created')
    title = models.CharField('عنوان پروژه', max_length=200)
    description = models.TextField('توضیحات')
    pricing_type = models.CharField('نوع قیمت‌گذاری', max_length=20, choices=PRICING_TYPES)
    budget = models.DecimalField('بودجه', max_digits=12, decimal_places=2)
    deadline = models.DateTimeField('مهلت تحویل', blank=True, null=True)
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'پروژه'
        verbose_name_plural = 'پروژه‌ها'
        db_table = 'projects'

    def __str__(self):
        return self.title


# ============================================================================
# ۱۰. جدول واسط دسته‌بندی پروژه‌ها (Project Categories)
# ============================================================================
class ProjectCategory(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'دسته‌بندی پروژه'
        verbose_name_plural = 'دسته‌بندی‌های پروژه‌ها'
        db_table = 'project_categories'
        unique_together = ('project', 'category')


# ============================================================================
# ۱۱. جدول واسط مهارت‌های پروژه (Project Skills)
# ============================================================================
class ProjectSkill(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    is_required = models.BooleanField('الزامی', default=True)

    class Meta:
        verbose_name = 'مهارت مورد نیاز پروژه'
        verbose_name_plural = 'مهارت‌های پروژه‌ها'
        db_table = 'project_skills'
        unique_together = ('project', 'skill')


# ============================================================================
# ۱۲. پیشنهادها (Proposals)
# ============================================================================
class Proposal(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار'),
        ('ACCEPTED', 'پذیرفته‌شده'),
        ('REJECTED', 'رد‌شده'),
        ('WITHDRAWN', 'انصراف'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='proposals')
    freelancer = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='proposals_submitted')
    bid_amount = models.DecimalField('مبلغ پیشنهادی', max_digits=12, decimal_places=2)
    estimated_duration = models.IntegerField('مدت تخمینی (روز/ساعت)', blank=True, null=True)
    cover_letter = models.TextField('متن پیشنهاد')
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'پیشنهاد'
        verbose_name_plural = 'پیشنهادها'
        db_table = 'proposals'
        unique_together = ('project', 'freelancer')

    def __str__(self):
        return f"Proposal #{self.id} for {self.project.title}"


# ============================================================================
# ۱۳. پیام‌ها و گفت‌وگوها (Messages)
# ============================================================================
class Message(models.Model):
    """مدل پیام‌های خصوصی، گفت‌وگوی پروژه و اعلان‌های قبولی پیشنهاد (FR-14)"""
    MESSAGE_TYPES = [
        ('DIRECT', 'پیام مستقیم'),
        ('PROPOSAL_ACCEPTED', 'پذیرش پیشنهاد'),
        ('PROJECT_UPDATE', 'به‌روزرسانی پروژه'),
        ('SYSTEM', 'پیام سیستم'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField('موضوع', max_length=200, blank=True, null=True)
    content = models.TextField('متن پیام')
    message_type = models.CharField('نوع پیام', max_length=30, choices=MESSAGE_TYPES, default='DIRECT')
    is_read = models.BooleanField('خوانده شده', default=False)
    created_at = models.DateTimeField('تاریخ ارسال', auto_now_add=True)

    class Meta:
        verbose_name = 'پیام'
        verbose_name_plural = 'پیام‌ها'
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message #{self.id} from {self.sender} to {self.receiver}"

