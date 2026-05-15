from django.db import migrations


POSTGRES_SCHEMA_FIX_SQL = [
    # thumbnail (ImageField -> varchar)
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='courses_course'
              AND column_name='thumbnail'
        ) THEN
            ALTER TABLE courses_course
            ADD COLUMN thumbnail varchar(100);
        END IF;
    END $$;
    """,
    # category_id FK
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='courses_course'
              AND column_name='category_id'
        ) THEN
            ALTER TABLE courses_course
            ADD COLUMN category_id bigint;
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.table_name='courses_course'
              AND tc.constraint_type='FOREIGN KEY'
              AND kcu.column_name='category_id'
        ) THEN
            ALTER TABLE courses_course
            ADD CONSTRAINT courses_course_category_id_fk
            FOREIGN KEY (category_id) REFERENCES courses_category (id)
            ON DELETE SET NULL;
        END IF;
    END $$;
    """,
    # created_at / updated_at (если таблица создавалась вручную)
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='courses_course'
              AND column_name='created_at'
        ) THEN
            ALTER TABLE courses_course
            ADD COLUMN created_at timestamp with time zone;
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='courses_course'
              AND column_name='updated_at'
        ) THEN
            ALTER TABLE courses_course
            ADD COLUMN updated_at timestamp with time zone;
        END IF;
    END $$;
    """,
]


def apply_postgres_schema_fix(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    for sql in POSTGRES_SCHEMA_FIX_SQL:
        schema_editor.execute(sql)


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(apply_postgres_schema_fix, migrations.RunPython.noop)
    ]
