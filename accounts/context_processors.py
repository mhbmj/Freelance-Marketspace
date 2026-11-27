from .models import Proposal


def notifications_processor(request):
    """کانتکست پروسسور برای اعلان‌های زنگوله و پیام‌های کارفرما به صورت سراسری در تمام صفحات"""
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'employer_received_proposals': [],
        }

    # فیلتر پایه برای پیشنهادهای ثبت‌شده روی پروژه‌های متعلق به این کاربر
    base_qs = Proposal.objects.filter(project__employer=request.user)
    unread_count = base_qs.filter(status='PENDING').count()

    # واکشی پیشنهادهای اخیر جهت نمایش در کشوی پیام‌ها
    received_proposals = list(
        base_qs.select_related('project', 'freelancer').order_by('-created_at')[:15]
    )

    return {
        'unread_notifications_count': unread_count,
        'employer_received_proposals': received_proposals,
    }
