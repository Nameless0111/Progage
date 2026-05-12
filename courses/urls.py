from django.urls import path
from . import views, teacher_views, api_views

app_name = 'courses'

urlpatterns = [
    # Основные URL
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/like/', views.toggle_like, name='toggle_like'),
    path('<int:course_id>/review/', views.submit_review, name='submit_review'),
    path('<int:course_id>/lesson/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
    path('<int:course_id>/lesson/<int:lesson_id>/complete/', views.complete_lesson, name='complete_lesson'),
    path('<int:course_id>/lesson/<int:lesson_id>/comment/', views.add_comment, name='add_comment'),
    
    # URL для преподавателей
    path('teacher/', teacher_views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/create/', teacher_views.create_course, name='teacher_create_course'),
    path('teacher/<int:course_id>/edit/', teacher_views.edit_course, name='teacher_edit_course'),
    path('teacher/<int:course_id>/delete/', teacher_views.delete_course, name='teacher_delete_course'),
    path('teacher/<int:course_id>/lessons/', teacher_views.course_lessons, name='teacher_course_lessons'),
    path('teacher/<int:course_id>/lessons/create/', teacher_views.create_lesson, name='teacher_create_lesson'),
    path('teacher/<int:course_id>/lessons/<int:lesson_id>/edit/', teacher_views.edit_lesson, name='teacher_edit_lesson'),
    path('teacher/<int:course_id>/lessons/<int:lesson_id>/delete/', teacher_views.delete_lesson, name='teacher_delete_lesson'),
    
    # URL для конструктора тестов
    path('teacher/lessons/<int:lesson_id>/test/', teacher_views.test_constructor, name='test_constructor'),
    path('teacher/lessons/<int:lesson_id>/test/<int:question_id>/edit/', teacher_views.edit_test_question, name='edit_test_question'),
    path('teacher/lessons/<int:lesson_id>/test/<int:question_id>/delete/', teacher_views.delete_test_question, name='delete_test_question'),
    
    # URL для прохождения тестов
    path('lesson/<int:lesson_id>/test/', views.take_test, name='take_test'),
    path('lesson/<int:lesson_id>/test/submit/', views.submit_test, name='submit_test'),
    path('lesson/<int:lesson_id>/test/<int:submission_id>/result/', views.test_result, name='test_result'),
    
    # URL для практических заданий
    path('teacher/lessons/<int:lesson_id>/practice/', teacher_views.practice_assignment, name='practice_assignment'),
    path('teacher/lessons/<int:lesson_id>/practice-manual/', teacher_views.practice_assignment_manual, name='practice_assignment_manual'),
    path('teacher/submissions/<int:submission_id>/review/', teacher_views.review_submission, name='review_submission'),
    path('lessons/<int:lesson_id>/submit/', teacher_views.submit_code, name='submit_code'),
    
    # API URLs
    path('api/test-code/', api_views.test_code, name='test_code_api'),
]
