from django.db import migrations


def get_columns(schema_editor, table_name):
    cursor = schema_editor.connection.cursor()
    return {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            cursor,
            table_name,
        )
    }


def quote(schema_editor, name):
    return schema_editor.connection.ops.quote_name(name)


def ensure_message_columns(apps, schema_editor):
    table_name = "chat_message"
    table = quote(schema_editor, table_name)
    columns = get_columns(schema_editor, table_name)

    if "content" not in columns:
        if "text" in columns:
            schema_editor.execute(
                f"ALTER TABLE {table} RENAME COLUMN {quote(schema_editor, 'text')} "
                f"TO {quote(schema_editor, 'content')}"
            )
        else:
            schema_editor.execute(
                f"ALTER TABLE {table} ADD COLUMN {quote(schema_editor, 'content')} text NOT NULL DEFAULT ''"
            )

    columns = get_columns(schema_editor, table_name)

    if "created_at" not in columns:
        if "timestamp" in columns:
            schema_editor.execute(
                f"ALTER TABLE {table} RENAME COLUMN {quote(schema_editor, 'timestamp')} "
                f"TO {quote(schema_editor, 'created_at')}"
            )
        elif schema_editor.connection.vendor == "postgresql":
            schema_editor.execute(
                f"ALTER TABLE {table} ADD COLUMN {quote(schema_editor, 'created_at')} "
                "timestamp with time zone NOT NULL DEFAULT NOW()"
            )
        else:
            schema_editor.execute(
                f"ALTER TABLE {table} ADD COLUMN {quote(schema_editor, 'created_at')} "
                "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0002_schema_state_sync"),
    ]

    operations = [
        migrations.RunPython(ensure_message_columns, migrations.RunPython.noop),
    ]
