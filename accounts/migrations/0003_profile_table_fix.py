from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_is_email_verified_state_sync"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                """
                CREATE TABLE IF NOT EXISTS accounts_profile (
                    id bigserial PRIMARY KEY,
                    learning_progress jsonb NOT NULL DEFAULT '{}'::jsonb,
                    achievements jsonb NOT NULL DEFAULT '[]'::jsonb,
                    preferences jsonb NOT NULL DEFAULT '{}'::jsonb,
                    user_id bigint NOT NULL UNIQUE
                );
                """,
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.table_constraints
                        WHERE table_name = 'accounts_profile'
                          AND constraint_type = 'FOREIGN KEY'
                    ) THEN
                        ALTER TABLE accounts_profile
                        ADD CONSTRAINT accounts_profile_user_id_fk
                        FOREIGN KEY (user_id) REFERENCES accounts_user(id)
                        ON DELETE CASCADE;
                    END IF;
                END $$;
                """,
            ],
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
