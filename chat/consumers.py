from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from .models import Message, SupportChat
from django.utils import timezone
from accounts.models import Notification

User = get_user_model()

predefined = {
    "Как выбрать подходящий курс?": "Для выбора курса учитывайте ваш уровень знаний, цели и время. Посмотрите описания курсов и отзывы.",
    "Проблема с оплатой": "Если проблема с оплатой, проверьте данные карты или свяжитесь с банком. Курсы бесплатны, но для премиум фич может требоваться оплата.",
}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        # Check if user has access to this chat
        try:
            chat = SupportChat.objects.get(id=self.chat_id)
            user = self.scope['user']
            if user != chat.user and user.role != 'admin':
                await self.close()
                return
        except SupportChat.DoesNotExist:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Filter out messages containing 'from'
        if 'from' in message.lower():
            return
        
        sender = self.scope['user']

        chat = SupportChat.objects.get(id=self.chat_id)
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
        if msg.sender.role == 'admin':
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
                Notification.objects.create(
                    user=admin, 
                    notification_type='new_chat_message',
                    title='Новое сообщение в поддержке',
                    message=f"Новое сообщение от {msg.sender.get_full_name() or msg.sender.username}: {msg.content[:50]}...",
                    chat_room_id=str(self.chat_id)
                )

        await self.channel_layer.group_send(
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
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': reply_text,
                    'sender': admin.username,
                    'sender_id': admin.id,
                    'timestamp': str(reply.created_at)
                }
            )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        sender_id = event['sender_id']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'sender_id': sender_id,
            'timestamp': timestamp
        }))
