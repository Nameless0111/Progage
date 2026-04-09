from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Колонка accounts_user.is_email_verified уже существует в БД (по текущей ошибке).
                # Обеспечим дефолт и отсутствие NULL на уровне БД.
                migrations.RunSQL(
                    sql=[
                        "UPDATE accounts_user SET is_email_verified = FALSE WHERE is_email_verified IS NULL;",
                        "ALTER TABLE accounts_user ALTER COLUMN is_email_verified SET DEFAULT FALSE;",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="user",
                    name="is_email_verified",
                    field=models.BooleanField(default=False),
                ),
            ],
        )
    ]
