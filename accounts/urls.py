from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('select-role/', views.select_role_view, name='select_role'),
    path('onboarding/categories/', views.onboarding_categories_view, name='onboarding_categories'),
    path('onboarding/skills/', views.onboarding_skills_view, name='onboarding_skills'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/notifications/', views.notifications_redirect_view, name='dashboard_notifications'),
    path('dashboard/messages/', views.messages_redirect_view, name='dashboard_messages'),
    path('profile/', views.profile_view, name='profile'),
    path('projects/', views.projects_list_view, name='projects_list'),
    path('projects/<int:project_id>/', views.project_detail_view, name='project_detail'),
    path('categories/', views.categories_view, name='categories'),
    path('freelancers/', views.freelancers_list_view, name='freelancers_list'),
    path('terms/', views.terms_view, name='terms'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.reset_password_confirm_view, name='reset_password'),
    path('welcome/', views.welcome_view, name='welcome'),
    path('coming-soon/', views.coming_soon_view, name='coming_soon'),
    path('logout/', views.logout_view, name='logout'),
]
