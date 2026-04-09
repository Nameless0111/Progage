from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Logging
    path('logs/activity/', views.activity_logs, name='activity_logs'),
    path('logs/system/', views.system_logs, name='system_logs'),
    path('logs/errors/', views.error_logs, name='error_logs'),
    path('logs/errors/<int:error_id>/resolve/', views.resolve_error, name='resolve_error'),
    path('logs/sessions/', views.user_sessions, name='user_sessions'),
    path('logs/popular/', views.popular_content, name='popular_content'),
    
    # Backups
    path('backups/', views.backup_logs, name='backup_logs'),
    path('backups/create/', views.create_backup, name='create_backup'),
    path('backups/<str:filename>/download/', views.download_backup, name='download_backup'),
    path('backups/<str:filename>/delete/', views.delete_backup, name='delete_backup'),
    path('backups/<str:filename>/restore/', views.restore_backup, name='restore_backup'),
    
    # Statistics
    path('statistics/', views.statistics, name='statistics'),
    
    # Users CRUD
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    
    # Courses CRUD
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:course_id>/delete/', views.course_delete, name='course_delete'),
    
    # Enrollments
    path('enrollments/', views.enrollment_list, name='enrollment_list'),
    path('enrollments/<int:enrollment_id>/delete/', views.enrollment_delete, name='enrollment_delete'),
    
    # Likes
    path('likes/', views.like_list, name='like_list'),
    path('likes/<int:like_id>/delete/', views.like_delete, name='like_delete'),
    
    # Reviews
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/<int:review_id>/delete/', views.review_delete, name='review_delete'),
]
