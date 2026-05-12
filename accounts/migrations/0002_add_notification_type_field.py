# Generated migration to add notification_type field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(max_length=20, default='system', choices=[
                ('new_chat', 'Новый чат'),
                ('new_chat_message', 'Новое сообщение в чате'),
                ('course_enrollment', 'Запись на курс'),
                ('course_review', 'Отзыв на курс'),
                ('system', 'Системное уведомление'),
            ]),
        ),
    ]
