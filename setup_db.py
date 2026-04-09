import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.db import connection

sql_commands = [
    """
    CREATE TABLE IF NOT EXISTS courses_category (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS courses_course (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        description TEXT NOT NULL,
        instructor_id INTEGER,
        category_id INTEGER REFERENCES courses_category(id) ON DELETE SET NULL,
        level VARCHAR(20) DEFAULT 'beginner' NOT NULL,
        price DECIMAL(10, 2) DEFAULT 0.00,
        thumbnail VARCHAR(100),
        is_published BOOLEAN DEFAULT FALSE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS courses_lesson (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        course_id INTEGER REFERENCES courses_course(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        video_url VARCHAR(500),
        "order" INTEGER DEFAULT 0,
        is_free BOOLEAN DEFAULT FALSE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS courses_courseenrollment (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        course_id INTEGER REFERENCES courses_course(id) ON DELETE CASCADE,
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        progress INTEGER DEFAULT 0,
        UNIQUE(user_id, course_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS courses_courselike (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        course_id INTEGER REFERENCES courses_course(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, course_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS courses_coursereview (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        course_id INTEGER REFERENCES courses_course(id) ON DELETE CASCADE,
        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, course_id)
    );
    """,
]

with connection.cursor() as cursor:
    for sql in sql_commands:
        try:
            cursor.execute(sql)
            print(f"Created table successfully")
        except Exception as e:
            print(f"Error: {e}")
    
    # Insert test categories
    cursor.execute("SELECT COUNT(*) FROM courses_category;")
    count = cursor.fetchone()[0]
    if count == 0:
        categories = [
            ('Python', 'Курсы по программированию на Python'),
            ('JavaScript', 'Веб-разработка и JavaScript'),
            ('Java', 'Курсы по Java и backend разработке'),
            ('Data Science', 'Анализ данных и машинное обучение'),
            ('Web Development', 'Веб-разработка и фреймворки'),
        ]
        for name, desc in categories:
            cursor.execute(
                "INSERT INTO courses_category (name, description) VALUES (%s, %s);",
                [name, desc]
            )
        print("Test categories created")

print("Database setup completed!")
