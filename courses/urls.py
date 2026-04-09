from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/like/', views.toggle_like, name='toggle_like'),
    path('<int:course_id>/review/', views.submit_review, name='submit_review'),
    path('<int:course_id>/lesson/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
]
