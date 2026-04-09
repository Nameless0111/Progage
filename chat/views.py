from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import SupportChat, Message
from accounts.models import User

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
        'messages': messages_list
    })

@login_required
@require_POST
def send_message(request, chat_id):
    chat = get_object_or_404(SupportChat, id=chat_id)
    
    # Проверка доступа
    if request.user.role != 'admin' and chat.user != request.user:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    content = request.POST.get('content')
    
    if content.strip():
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            content=content.strip()
        )
        chat.updated_at = message.created_at
        chat.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.created_at.strftime('%H:%M'),
                'sender': message.sender.username,
                'is_own': True
            }
        })
    
    return JsonResponse({'success': False, 'error': 'Empty message'})

@login_required
def start_chat(request):
    if request.user.role == 'admin':
        messages.error(request, 'Администраторы не могут создавать чаты')
        return redirect('chat:chat_list')
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        if subject.strip():
            chat = SupportChat.objects.create(
                user=request.user,
                subject=subject.strip()
            )
            messages.success(request, 'Чат создан')
            return redirect('chat:chat_detail', chat_id=chat.id)
    
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
