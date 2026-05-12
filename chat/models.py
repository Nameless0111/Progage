from django.db import models
from accounts.models import User

class SupportChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_chats')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='admin_chats')
    subject = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('closed', 'Closed')], default='open')
    priority = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat {self.id} - {self.user.username}"

class Message(models.Model):
    chat = models.ForeignKey(SupportChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message {self.id}"
