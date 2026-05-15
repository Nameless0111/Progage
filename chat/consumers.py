from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from django.contrib.auth import get_user_model
from .models import Message, SupportChat
from django.utils import timezone
from accounts.models import Notification, UserNotifications

User = get_user_model()

predefined = {
    "Как выбрать подходящий курс?": "Для выбора курса учитывайте ваш уровень знаний, цели и время. Посмотрите описания курсов и отзывы.",
    "Вопрос по курсу": "Все курсы на платформе бесплатные. Если курс не открывается, проверьте авторизацию и запись на курс.",
}


def wants_support_notification(user):
    settings, _ = UserNotifications.objects.get_or_create(user=user)
    return settings.support_messages

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        # Check if user has access to this chat
        try:
            chat = SupportChat.objects.get(id=self.chat_id)
            user = self.scope['user']
            if user != chat.user and user.role != 'admin':
                self.close()
                return
        except SupportChat.DoesNotExist:
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message = (text_data_json.get('message') or '').strip()
        if not message:
            return
        
        sender = self.scope['user']

        chat = SupportChat.objects.get(id=self.chat_id)
        if chat.status == 'closed':
            return

        msg = Message.objects.create(chat=chat, sender=sender, content=message)

        # Auto reply for predefined questions
        reply_text = None
        if msg.content in predefined:
            admin = chat.admin or User.objects.filter(role='admin').first()
            if admin:
                reply_text = predefined[msg.content]
                reply = Message.objects.create(chat=chat, sender=admin, content=reply_text)
                chat.updated_at = timezone.now()
                chat.save()
        elif msg.content == "Другая проблема":
            chat.priority = True
            chat.save()

        # Create notification for user if admin sent message
        if msg.sender.role == 'admin' and wants_support_notification(chat.user):
            Notification.objects.create(
                user=chat.user, 
                notification_type='new_chat_message',
                title='Ответ администратора',
                message=f"Администратор {msg.sender.get_full_name() or msg.sender.username} ответил: {msg.content[:50]}...",
                chat_room_id=str(self.chat_id)
            )
        
        # Create notification for all admins if user sent message
        elif msg.sender == chat.user:
            admins = User.objects.filter(role='admin')
            for admin in admins:
                if not wants_support_notification(admin):
                    continue
                Notification.objects.create(
                    user=admin, 
                    notification_type='new_chat_message',
                    title='Новое сообщение в поддержке',
                    message=f"Новое сообщение от {msg.sender.get_full_name() or msg.sender.username}: {msg.content[:50]}...",
                    chat_room_id=str(self.chat_id)
                )

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.username,
                'sender_id': sender.id,
                'timestamp': str(msg.created_at)
            }
        )

        # Send auto reply if any
        if reply_text:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': reply_text,
                    'sender': admin.username,
                    'sender_id': admin.id,
                    'timestamp': str(reply.created_at)
                }
            )

    def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        sender_id = event['sender_id']
        timestamp = event['timestamp']

        self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'sender_id': sender_id,
            'timestamp': timestamp
        }))
