from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('select-role/', views.select_role_view, name='select_role'),
    path('onboarding/categories/', views.onboarding_categories_view, name='onboarding_categories'),
    path('onboarding/skills/', views.onboarding_skills_view, name='onboarding_skills'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.reset_password_confirm_view, name='reset_password'),
    path('welcome/', views.welcome_view, name='welcome'),
    path('coming-soon/', views.coming_soon_view, name='coming_soon'),
    path('logout/', views.logout_view, name='logout'),
]
