from django.db import migrations


DEFAULT_CATEGORIES = [
    ("Программирование", "Базовые и продвинутые курсы по программированию."),
    ("Веб-разработка", "Создание веб-приложений, интерфейсов и серверной логики."),
    ("Базы данных", "Проектирование, хранение и обработка данных."),
    ("Алгоритмы", "Алгоритмическое мышление и решение задач."),
    ("Разработка ПО", "Практика создания и сопровождения программных систем."),
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("courses", "Category")
    for name, description in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            name=name,
            defaults={"description": description},
        )


def unseed_categories(apps, schema_editor):
    Category = apps.get_model("courses", "Category")
    Category.objects.filter(name__in=[name for name, _ in DEFAULT_CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0015_free_published_by_default"),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed_categories),
    ]
