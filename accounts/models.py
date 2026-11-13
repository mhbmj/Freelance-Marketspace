from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """مدیریت ایجاد کاربران با ایمیل به عنوان شناسه اصلی"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('ایمیل الزامی است.')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)  # استفاده از الگوریتم امن PBKDF2
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """مدل کاربر سامانه فریلنسری منطبق با پایگاه داده"""

    first_name = models.CharField('نام', max_length=50)
    last_name = models.CharField('نام خانوادگی', max_length=50)
    email = models.EmailField('ایمیل', unique=True)
    phone_number = models.CharField('شماره موبایل', max_length=20, blank=True, null=True)

    STATUS_CHOICES = [
        ('ACTIVE', 'فعال'),
        ('INACTIVE', 'غیرفعال'),
        ('SUSPENDED', 'مسدود'),
    ]
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    is_active = models.BooleanField('فعال', default=True)
    is_staff = models.BooleanField('دسترسی ادمین', default=False)
    created_at = models.DateTimeField('تاریخ ثبت‌نام', auto_now_add=True)
    updated_at = models.DateTimeField('آخرین ویرایش', auto_now=True)

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
