from django.db import migrations, models


def make_learning_content_free(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    Lesson = apps.get_model('courses', 'Lesson')
    PracticeAssignment = apps.get_model('courses', 'PracticeAssignment')

    Course.objects.update(price=0, is_published=True)
    Lesson.objects.update(is_free=True)
    PracticeAssignment.objects.update(is_published=True)


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0014_courseenrollment_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='is_published',
            field=models.BooleanField(default=True, verbose_name='Опубликован'),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='is_free',
            field=models.BooleanField(default=True, verbose_name='Бесплатный'),
        ),
        migrations.AlterField(
            model_name='practiceassignment',
            name='is_published',
            field=models.BooleanField(default=True, verbose_name='Опубликовано'),
        ),
        migrations.RunPython(make_learning_content_free, migrations.RunPython.noop),
    ]
