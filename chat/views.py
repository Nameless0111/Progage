from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from .models import SupportChat, Message
from accounts.models import User, UserNotifications


def wants_support_notification(user):
    settings, _ = UserNotifications.objects.get_or_create(user=user)
    return settings.support_messages

@login_required
def chat_list(request):
    if request.user.role == 'admin':
        chats = SupportChat.objects.all().order_by('-updated_at')
    else:
        chats = SupportChat.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'chat/chat_list.html', {'chats': chats})

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(SupportChat, id=chat_id)
    
    # Проверка доступа
    if request.user.role != 'admin' and chat.user != request.user:
        messages.error(request, 'У вас нет доступа к этому чату')
        return redirect('chat:chat_list')
    
    messages_list = chat.messages.all().order_by('created_at')
    
    # Помечаем сообщения как прочитанные
    if request.user.role == 'admin':
        unread_messages = messages_list.filter(is_read=False).exclude(sender=request.user)
        unread_messages.update(is_read=True)
    else:
        unread_messages = messages_list.filter(is_read=False, sender__role='admin')
        unread_messages.update(is_read=True)
    
    return render(request, 'chat/chat_detail.html', {
        'chat': chat,
        'chat_messages': messages_list
    })

@login_required
@require_POST
def send_message(request, chat_id):
    chat = get_object_or_404(SupportChat, id=chat_id)
    
    # Проверка доступа
    if request.user.role != 'admin' and chat.user != request.user:
        messages.error(request, 'У вас нет доступа к этому чату')
        return redirect('chat:chat_detail', chat_id=chat_id)
    
    content = (request.POST.get('content') or '').strip()
    
    if chat.status == 'closed':
        messages.error(request, 'Чат закрыт. Создайте новое обращение или попросите администратора открыть чат.')
        return redirect('chat:chat_detail', chat_id=chat_id)

    if content:
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            content=content
        )
        chat.updated_at = message.created_at
        chat.save()
        
        # Добавляем уведомления для всех участников чата
        from accounts.models import User, Notification
        
        # Если сообщение от пользователя - уведомляем админов
        if request.user.role != 'admin':
            admins = User.objects.filter(role='admin')
            for admin in admins:
                if not wants_support_notification(admin):
                    continue
                notification = Notification(
                    user=admin,
                    notification_type='new_chat_message',
                    title=f'Новое сообщение в чате "{chat.subject}"',
                    message=f'Пользователь {request.user.get_full_name() or request.user.username} отправил сообщение: {content[:100]}...',
                    chat_room_id=str(chat_id)
                )
                notification.save()
        # Если сообщение от админа - уведомляем пользователя чата
        else:
            if wants_support_notification(chat.user):
                notification = Notification(
                    user=chat.user,
                    notification_type='new_chat_message',
                    title=f'Ответ администратора в чате "{chat.subject}"',
                    message=f'Администратор {request.user.get_full_name() or request.user.username} ответил: {content[:100]}...',
                    chat_room_id=str(chat_id)
                )
                notification.save()
    else:
        messages.error(request, 'Сообщение не может быть пустым')
        return redirect('chat:chat_detail', chat_id=chat_id)
    
    messages.success(request, 'Сообщение отправлено')
    return redirect('chat:chat_detail', chat_id=chat_id)

@login_required
def refresh_chat(request, chat_id):
    """AJAX endpoint для обновления чата в реальном времени"""
    chat = get_object_or_404(SupportChat, id=chat_id)
    
    # Проверка доступа
    if request.user.role != 'admin' and chat.user != request.user:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    # Получаем последние сообщения (за последние 5 минут)
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    recent_messages = chat.messages.filter(
        created_at__gte=five_minutes_ago
    ).order_by('created_at').values(
        'id', 'content', 'created_at', 'sender__username'
    )
    
    # Форматируем сообщения
    messages_data = []
    for msg in recent_messages:
        messages_data.append({
            'id': msg['id'],
            'content': msg['content'],
            'timestamp': msg['created_at'].strftime('%H:%M'),
            'sender': msg['sender__username']
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data
    })

@login_required
def start_chat(request):
    if request.user.role == 'admin':
        messages.error(request, 'Администраторы не могут создавать чаты')
        return redirect('chat:chat_list')
    
    if request.method == 'POST':
        subject = (request.POST.get('subject') or '').strip()
        if subject:
            chat = SupportChat.objects.create(
                user=request.user,
                subject=subject
            )
            
            # Уведомляем администраторов о новом чате
            from accounts.models import User, Notification
            
            admins = User.objects.filter(role='admin')
            for admin in admins:
                if not wants_support_notification(admin):
                    continue
                notification = Notification(
                    user=admin,
                    notification_type='new_chat',
                    title=f'Новый чат поддержки',
                    message=f'Пользователь {request.user.get_full_name() or request.user.username} создал чат "{subject}"'
                )
                notification.save()
            
            messages.success(request, 'Чат создан')
            return redirect('chat:chat_detail', chat_id=chat.id)
        messages.error(request, 'Тема обращения не может быть пустой')
    
    return render(request, 'chat/start_chat.html')

@login_required
@require_POST
def close_chat(request, chat_id):
    chat = get_object_or_404(SupportChat, id=chat_id)
    
    if request.user.role != 'admin':
        messages.error(request, 'Только администратор может закрыть чат')
        return redirect('chat:chat_detail', chat_id=chat_id)
    
    chat.status = 'closed'
    chat.save()
    messages.success(request, 'Чат закрыт')
    return redirect('chat:chat_detail', chat_id=chat_id)
