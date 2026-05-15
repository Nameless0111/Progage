from django.db import migrations, models


SUPPORTED_LANGUAGES = [
    ("python", "Python"),
    ("javascript", "JavaScript"),
    ("java", "Java"),
    ("cpp", "C++"),
    ("c", "C"),
]


def normalize_language_rows(apps, schema_editor):
    PracticeAssignment = apps.get_model("courses", "PracticeAssignment")
    SecurityConfig = apps.get_model("courses", "SecurityConfig")
    supported_codes = [code for code, _label in SUPPORTED_LANGUAGES]

    PracticeAssignment.objects.exclude(
        programming_language__in=supported_codes
    ).update(programming_language="python")
    SecurityConfig.objects.exclude(
        programming_language__in=supported_codes
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0016_seed_default_categories"),
    ]

    operations = [
        migrations.RunPython(normalize_language_rows, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="practiceassignment",
            name="programming_language",
            field=models.CharField(
                choices=SUPPORTED_LANGUAGES,
                max_length=20,
                verbose_name="Язык программирования",
            ),
        ),
        migrations.AlterField(
            model_name="securityconfig",
            name="programming_language",
            field=models.CharField(
                choices=SUPPORTED_LANGUAGES,
                max_length=20,
                unique=True,
                verbose_name="Язык программирования",
            ),
        ),
    ]
