from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # DB уже содержит chat_message(content, created_at) и chat_supportchat без subject.
                migrations.RunSQL(
                    sql=[
                        """
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1
                                FROM information_schema.columns
                                WHERE table_name='chat_supportchat'
                                  AND column_name='subject'
                            ) THEN
                                ALTER TABLE chat_supportchat
                                ADD COLUMN subject varchar(255) NOT NULL DEFAULT '';
                            END IF;
                        END $$;
                        """,
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="supportchat",
                    name="subject",
                    field=models.CharField(blank=True, default="", max_length=255),
                ),
                # Синхронизируем состояние Django с реальными названиями колонок в БД
                migrations.RenameField(
                    model_name="message",
                    old_name="text",
                    new_name="content",
                ),
                migrations.RenameField(
                    model_name="message",
                    old_name="timestamp",
                    new_name="created_at",
                ),
            ],
        )
    ]
