from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0002_schema_fix"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # courses_course.is_published
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name='courses_course'
                          AND column_name='is_published'
                    ) THEN
                        ALTER TABLE courses_course
                        ADD COLUMN is_published boolean NOT NULL DEFAULT FALSE;
                    END IF;
                END $$;
                """,
                # courses_lesson.is_free
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name='courses_lesson'
                          AND column_name='is_free'
                    ) THEN
                        ALTER TABLE courses_lesson
                        ADD COLUMN is_free boolean NOT NULL DEFAULT FALSE;
                    END IF;
                END $$;
                """,
            ],
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
