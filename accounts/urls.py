from django.urls import path
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetCompleteView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('teachers/', views.teachers_list, name='teachers_list'),
    path('teachers/<int:teacher_id>/', views.teacher_profile, name='teacher_profile'),
    path('test-stars/', views.test_stars, name='test_stars'),
    path('certificates/', views.certificates, name='certificates'),
    # Password reset URLs
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
    # Two-factor authentication URLs
    path('2fa/', views.two_factor_verify, name='two_factor_verify'),
    path('2fa/setup/', views.two_factor_setup, name='two_factor_setup'),
    # Settings URLs
    path('settings/', views.settings, name='settings'),
    # 2FA API endpoints
    path('generate-2fa-secret/', views.generate_2fa_secret, name='generate_2fa_secret'),
    path('verify-2fa-setup/', views.verify_2fa_setup, name='verify_2fa_setup'),
    path('enable-2fa/', views.enable_2fa, name='enable_2fa'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),
    path('regenerate-backup-codes/', views.regenerate_backup_codes, name='regenerate_backup_codes'),
    path('reset-2fa/', views.reset_2fa, name='reset_2fa'),
    path('change-password/', views.change_password, name='change_password'),
    path('logout-all/', views.logout_all, name='logout_all'),
    # Additional settings URLs
    path('update-notifications/', views.update_notifications, name='update_notifications'),
    path('update-privacy/', views.update_privacy, name='update_privacy'),
]
