from django.db import migrations


JAVA_COMPILE_COMMAND = (
    "javac -J-Xmx256m -J-XX:ReservedCodeCacheSize=32m "
    "-J-XX:MaxMetaspaceSize=128m {file}"
)
JAVA_RUN_COMMAND = (
    "java -Xmx256m -XX:ReservedCodeCacheSize=32m "
    "-XX:MaxMetaspaceSize=128m {filename}"
)


def tune_security_configs(apps, schema_editor):
    SecurityConfig = apps.get_model("courses", "SecurityConfig")
    SecurityConfig.objects.filter(programming_language="java").update(
        compile_command=JAVA_COMPILE_COMMAND,
        run_command=JAVA_RUN_COMMAND,
        max_memory=4096,
    )
    SecurityConfig.objects.filter(programming_language="javascript").update(
        max_memory=4096,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0017_limit_practice_languages"),
    ]

    operations = [
        migrations.RunPython(tune_security_configs, migrations.RunPython.noop),
    ]
