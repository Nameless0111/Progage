from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_notification_lesson'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprivacy',
            name='anonymous_mode',
            field=models.BooleanField(default=False, verbose_name='Анонимный режим'),
        ),
        migrations.AddField(
            model_name='userprivacy',
            name='show_in_teachers_list',
            field=models.BooleanField(default=True, verbose_name='Показывать в списке преподавателей'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('new_chat', 'Новый чат'),
                    ('new_chat_message', 'Новое сообщение в чате'),
                    ('course_enrollment', 'Запись на курс'),
                    ('course_review', 'Отзыв на курс'),
                    ('new_lesson', 'Новый урок'),
                    ('support_messages', 'Сообщение поддержки'),
                    ('system', 'Системное уведомление'),
                ],
                max_length=20,
            ),
        ),
    ]
