from django.db import migrations, models


def get_columns(schema_editor, table_name):
    cursor = schema_editor.connection.cursor()
    return {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            cursor,
            table_name,
        )
    }


def sync_chat_columns(apps, schema_editor):
    support_columns = get_columns(schema_editor, "chat_supportchat")
    if "subject" not in support_columns:
        schema_editor.execute(
            "ALTER TABLE chat_supportchat "
            "ADD COLUMN subject varchar(255) NOT NULL DEFAULT ''"
        )

    message_columns = get_columns(schema_editor, "chat_message")
    if "content" not in message_columns and "text" in message_columns:
        schema_editor.execute("ALTER TABLE chat_message RENAME COLUMN text TO content")

    message_columns = get_columns(schema_editor, "chat_message")
    if "created_at" not in message_columns and "timestamp" in message_columns:
        schema_editor.execute("ALTER TABLE chat_message RENAME COLUMN timestamp TO created_at")


def add_subject_column_if_missing(apps, schema_editor):
    """Backward-compatible wrapper kept for old migration references."""
    table_name = "chat_supportchat"
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(),
            table_name,
        )
    }
    if "subject" in existing_columns:
        return

    schema_editor.execute(
        "ALTER TABLE chat_supportchat "
        "ADD COLUMN subject varchar(255) NOT NULL DEFAULT ''"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(sync_chat_columns, migrations.RunPython.noop)
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
