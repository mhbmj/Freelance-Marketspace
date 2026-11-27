from django import template
import datetime

register = template.Library()

JALALI_MONTHS = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
]

PERSIAN_DIGITS_MAP = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def gregorian_to_jalali(gy, gm, gd):
    """الگوریتم دقیق تبدیل تاریخ میلادی به تقویم هجری شمسی بدون وابستگی خارجی"""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy if gm > 2 else gy - 1
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


@register.filter(name='to_fa')
def to_fa(val):
    """تبدیل اعداد انگلیسی به ارقام فارسی"""
    if val is None:
        return ''
    return str(val).translate(PERSIAN_DIGITS_MAP)


@register.filter(name='price_format')
def price_format(val):
    """جدا کردن ۳ رقم ۳ رقم مبالغ با اعداد فارسی (مثال: ۴۰,۰۰۰,۰۰۰)"""
    if not val:
        return '۰'
    try:
        num = int(float(val))
        formatted = f"{num:,}"
        return formatted.translate(PERSIAN_DIGITS_MAP)
    except (ValueError, TypeError):
        return str(val)


@register.filter(name='price_en')
def price_en(val):
    """جدا کردن ۳ رقم ۳ رقم با اعداد انگلیسی (مثال: 40,000,000)"""
    if not val:
        return '0'
    try:
        num = int(float(val))
        return f"{num:,}"
    except (ValueError, TypeError):
        return str(val)


@register.filter(name='to_jalali')
def to_jalali(dt):
    """تبدیل تاریخ به شمسی با نام ماه و اعداد فارسی (مثال: ۶ آذر ۱۴۰۵)"""
    if not dt:
        return ''
    if isinstance(dt, datetime.datetime):
        dt = dt.date()
    elif not isinstance(dt, datetime.date):
        return str(dt)

    jy, jm, jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    month_name = JALALI_MONTHS[jm - 1]
    res = f"{jd} {month_name} {jy}"
    return res.translate(PERSIAN_DIGITS_MAP)
