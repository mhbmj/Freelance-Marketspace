from .models import Proposal, Message


def notifications_processor(request):
    """کانتکست پروسسور برای اعلان‌های زنگوله و پیام‌های کشویی کارفرما و فریلنسر به صورت سراسری"""
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'employer_received_proposals': [],
            'freelancer_accepted_proposals': [],
            'user_received_messages': [],
        }

    # ۱. پیشنهادهای دریافتی کارفرما (بر روی پروژه‌های متعلق به این کاربر)
    base_qs = Proposal.objects.filter(project__employer=request.user)
    employer_unread = base_qs.filter(status='PENDING').count()
    received_proposals = list(
        base_qs.select_related('project', 'freelancer').order_by('-created_at')[:15]
    )

    # ۲. پیام‌های دریافتی کاربر (شامل پیام‌های قبولی پیشنهاد، سیستم و مکالمات)
    user_messages_qs = Message.objects.filter(receiver=request.user).select_related('sender', 'project').order_by('-created_at')
    unread_messages_count = user_messages_qs.filter(is_read=False).count()
    user_received_messages = list(user_messages_qs[:20])

    # ۳. پیشنهادهای پذیرفته‌شده فریلنسر جهت نمایش سریع
    freelancer_qs = Proposal.objects.filter(freelancer=request.user, status='ACCEPTED')
    accepted_proposals = list(
        freelancer_qs.select_related('project', 'project__employer').order_by('-created_at')[:15]
    )

    total_unread = employer_unread + unread_messages_count

    return {
        'unread_notifications_count': total_unread,
        'employer_received_proposals': received_proposals,
        'freelancer_accepted_proposals': accepted_proposals,
        'user_received_messages': user_received_messages,
    }

