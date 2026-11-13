from django import forms
from django.contrib.auth import authenticate
from .models import User


class LoginForm(forms.Form):
    """فرم ورود به سامانه با پیام خطای امن و عمومی"""
    email = forms.EmailField(
        label='ایمیل',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'example@email.com',
            'id': 'email',
            'autocomplete': 'email',
            'required': True
        })
    )
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input input-with-toggle',
            'placeholder': 'رمز عبور خود را وارد کنید',
            'id': 'password',
            'autocomplete': 'current-password',
            'required': True
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            email_normalized = email.strip().lower()
            user = authenticate(email=email_normalized, password=password)
            if user is None:
                # طبق مشخصات تکلیف: پیام خطا نباید مشخص کند کدام یک اشتباه است
                raise forms.ValidationError('ایمیل یا رمز عبور اشتباه است.')
            if not user.is_active or user.status == 'SUSPENDED':
                raise forms.ValidationError('این حساب کاربری غیرفعال یا مسدود است.')
            cleaned_data['user'] = user

        return cleaned_data


class SignupForm(forms.ModelForm):
    """فرم ثبت‌نام و ایجاد حساب کاربری جدید با هش امن PBKDF2"""
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input input-with-toggle',
            'placeholder': 'حداقل ۶ کاراکتر',
            'id': 'password',
            'required': True
        })
    )
    password_confirm = forms.CharField(
        label='تکرار رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input input-with-toggle',
            'placeholder': 'تکرار رمز عبور',
            'id': 'password_confirm',
            'required': True
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'مثال: مهتاب',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'مثال: مروج',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'mahtabmj96@gmail.com',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '۰۹۲۲۴۲۹۴۸۳۳ (اختیاری)',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('این ایمیل قبلاً در سیستم ثبت شده است.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', 'رمز عبور و تکرار آن یکسان نیستند.')
            elif len(password) < 6:
                self.add_error('password', 'رمز عبور باید حداقل ۶ کاراکتر باشد.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data['password']
        # هش کردن رمز عبور در بک‌اند با الگوریتم امن PBKDF2
        user.set_password(password)
        if commit:
            user.save()
        return user


class ForgotPasswordForm(forms.Form):
    """فرم درخواست بازیابی رمز عبور"""
    email = forms.EmailField(
        label='ایمیل حساب کاربری',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'ایمیل ثبت‌شده خود را وارد کنید',
            'required': True
        })
    )

    def clean_email(self):
        return self.cleaned_data.get('email').strip().lower()


class ResetPasswordForm(forms.Form):
    """فرم تعیین رمز عبور جدید"""
    new_password = forms.CharField(
        label='رمز عبور جدید',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input input-with-toggle',
            'placeholder': 'حداقل ۶ کاراکتر',
            'id': 'new_password',
            'required': True
        })
    )
    new_password_confirm = forms.CharField(
        label='تکرار رمز عبور جدید',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input input-with-toggle',
            'placeholder': 'تکرار رمز عبور جدید',
            'id': 'new_password_confirm',
            'required': True
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('new_password_confirm')

        if p1 and p2:
            if p1 != p2:
                self.add_error('new_password_confirm', 'رمز عبور جدید و تکرار آن یکسان نیستند.')
            elif len(p1) < 6:
                self.add_error('new_password', 'رمز عبور جدید باید حداقل ۶ کاراکتر باشد.')

        return cleaned_data
