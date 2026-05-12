# Generated migration to add notification title field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_add_notification_type_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='title',
            field=models.CharField(max_length=200, default='Уведомление'),
        ),
    ]
