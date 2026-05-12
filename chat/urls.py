from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('support/', views.start_chat, name='support'),
    path('<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('<int:chat_id>/send/', views.send_message, name='send_message'),
    path('<int:chat_id>/refresh/', views.refresh_chat, name='refresh_chat'),
    path('start/', views.start_chat, name='start_chat'),
    path('<int:chat_id>/close/', views.close_chat, name='close_chat'),
]
