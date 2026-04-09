DROP DATABASE IF EXISTS progage_db;

CREATE DATABASE progage_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

\c progage_db;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

CREATE TABLE accounts_user (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP,
    is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    is_staff BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(10) DEFAULT 'student' NOT NULL,
    avatar VARCHAR(100),
    bio TEXT,
    phone VARCHAR(20),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES accounts_user(id) ON DELETE CASCADE,
    learning_progress JSONB DEFAULT '{}',
    achievements JSONB DEFAULT '[]',
    preferences JSONB DEFAULT '{}'
);

CREATE TABLE courses_category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses_course (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    instructor_id INTEGER REFERENCES accounts_user(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES courses_category(id) ON DELETE SET NULL,
    level VARCHAR(20) DEFAULT 'beginner' NOT NULL,
    price DECIMAL(10, 2) DEFAULT 0.00,
    thumbnail VARCHAR(100),
    is_published BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses_lesson (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    course_id INTEGER REFERENCES courses_course(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    video_url VARCHAR(500),
    "order" INTEGER DEFAULT 0,
    is_free BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses_courseenrollment (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES accounts_user(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses_course(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    progress INTEGER DEFAULT 0,
    UNIQUE(user_id, course_id)
);

CREATE TABLE courses_courselike (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES accounts_user(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses_course(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, course_id)
);

CREATE TABLE courses_coursereview (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES accounts_user(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses_course(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, course_id)
);

CREATE TABLE chat_supportchat (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES accounts_user(id) ON DELETE CASCADE,
    subject VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'open' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_to INTEGER REFERENCES accounts_user(id) ON DELETE SET NULL
);

CREATE TABLE chat_message (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER REFERENCES chat_supportchat(id) ON DELETE CASCADE,
    sender_id INTEGER REFERENCES accounts_user(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE adminpanel_activitylog (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES accounts_user(id) ON DELETE CASCADE,
    action_type VARCHAR(20) NOT NULL,
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    object_type VARCHAR(50),
    object_id INTEGER,
    object_repr VARCHAR(200),
    details JSONB DEFAULT '{}'
);

CREATE TABLE adminpanel_systemlog (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    module VARCHAR(100),
    function VARCHAR(100),
    line_number INTEGER,
    user_id INTEGER REFERENCES accounts_user(id) ON DELETE SET NULL,
    ip_address INET,
    request_id VARCHAR(50),
    extra_data JSONB DEFAULT '{}'
);

CREATE TABLE adminpanel_errorlog (
    id SERIAL PRIMARY KEY,
    error_type VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    stack_trace TEXT,
    url VARCHAR(500),
    method VARCHAR(10),
    user_id INTEGER REFERENCES accounts_user(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE NOT NULL,
    resolved_at TIMESTAMP,
    resolved_by INTEGER REFERENCES accounts_user(id) ON DELETE SET NULL
);

CREATE INDEX idx_accounts_user_email ON accounts_user(email);
CREATE INDEX idx_accounts_user_username ON accounts_user(username);
CREATE INDEX idx_accounts_user_role ON accounts_user(role);
CREATE INDEX idx_accounts_user_is_active ON accounts_user(is_active);

CREATE INDEX idx_courses_course_instructor ON courses_course(instructor_id);
CREATE INDEX idx_courses_course_category ON courses_course(category_id);
CREATE INDEX idx_courses_course_level ON courses_course(level);
CREATE INDEX idx_courses_course_is_published ON courses_course(is_published);
CREATE INDEX idx_courses_course_created_at ON courses_course(created_at);

CREATE INDEX idx_courses_lesson_course ON courses_lesson(course_id);
CREATE INDEX idx_courses_lesson_order ON courses_lesson("order");

CREATE INDEX idx_courses_enrollment_user ON courses_courseenrollment(user_id);
CREATE INDEX idx_courses_enrollment_course ON courses_courseenrollment(course_id);
CREATE INDEX idx_courses_enrollment_enrolled_at ON courses_courseenrollment(enrolled_at);

CREATE INDEX idx_courses_like_course ON courses_courselike(course_id);
CREATE INDEX idx_courses_review_course ON courses_coursereview(course_id);
CREATE INDEX idx_courses_review_rating ON courses_coursereview(rating);

CREATE INDEX idx_chat_supportchat_user ON chat_supportchat(user_id);
CREATE INDEX idx_chat_supportchat_status ON chat_supportchat(status);
CREATE INDEX idx_chat_message_chat ON chat_message(chat_id);
CREATE INDEX idx_chat_message_timestamp ON chat_message(timestamp);

CREATE INDEX idx_activitylog_user ON adminpanel_activitylog(user_id);
CREATE INDEX idx_activitylog_action_time ON adminpanel_activitylog(action_time);
CREATE INDEX idx_activitylog_action_type ON adminpanel_activitylog(action_type);

CREATE INDEX idx_systemlog_timestamp ON adminpanel_systemlog(timestamp);
CREATE INDEX idx_systemlog_level ON adminpanel_systemlog(level);
CREATE INDEX idx_systemlog_module ON adminpanel_systemlog(module);

CREATE INDEX idx_errorlog_timestamp ON adminpanel_errorlog(timestamp);
CREATE INDEX idx_errorlog_error_type ON adminpanel_errorlog(error_type);
CREATE INDEX idx_errorlog_resolved ON adminpanel_errorlog(resolved);

INSERT INTO accounts_user (username, email, first_name, last_name, password, is_superuser, is_staff, is_active, role, date_joined) VALUES
('admin', 'admin@progage.com', 'Администратор', 'Системы', 'pbkdf2_sha256$600000$abc123$def456', TRUE, TRUE, TRUE, 'admin', CURRENT_TIMESTAMP),
('teacher1', 'teacher1@progage.com', 'Иван', 'Петров', 'pbkdf2_sha256$600000$abc123$def456', FALSE, TRUE, TRUE, 'teacher', CURRENT_TIMESTAMP),
('teacher2', 'teacher2@progage.com', 'Мария', 'Иванова', 'pbkdf2_sha256$600000$abc123$def456', FALSE, TRUE, TRUE, 'teacher', CURRENT_TIMESTAMP),
('student1', 'student1@progage.com', 'Алексей', 'Смирнов', 'pbkdf2_sha256$600000$abc123$def456', FALSE, FALSE, TRUE, 'student', CURRENT_TIMESTAMP),
('student2', 'student2@progage.com', 'Елена', 'Козлова', 'pbkdf2_sha256$600000$abc123$def456', FALSE, FALSE, TRUE, 'student', CURRENT_TIMESTAMP),
('student3', 'student3@progage.com', 'Дмитрий', 'Новиков', 'pbkdf2_sha256$600000$abc123$def456', FALSE, FALSE, TRUE, 'student', CURRENT_TIMESTAMP);

INSERT INTO accounts_profile (user_id, learning_progress, achievements, preferences) VALUES
(1, '{"courses_completed": 0, "total_hours": 0}', '["first_login"]', '{"theme": "light", "notifications": true}'),
(2, '{"courses_completed": 5, "total_hours": 120}', '["top_teacher", "100_students"]', '{"theme": "dark", "notifications": true}'),
(3, '{"courses_completed": 3, "total_hours": 85}', '["top_teacher", "popular_instructor"]', '{"theme": "light", "notifications": false}'),
(4, '{"courses_completed": 2, "total_hours": 45}', '["first_course", "active_learner"]', '{"theme": "light", "notifications": true}'),
(5, '{"courses_completed": 1, "total_hours": 25}', '["first_course"]', '{"theme": "light", "notifications": true}'),
(6, '{"courses_completed": 0, "total_hours": 0}', '["first_login"]', '{"theme": "light", "notifications": true}');

INSERT INTO courses_category (name, description) VALUES
('Программирование', 'Курсы по различным языкам программирования и технологиям разработки'),
('Дизайн', 'Курсы по графическому дизайну, UI/UX и веб-дизайну'),
('Маркетинг', 'Курсы по цифровому маркетингу, SEO и SMM'),
('Бизнес', 'Курсы по предпринимательству, менеджменту и финансам'),
('Языки', 'Курсы по изучению иностранных языков');

INSERT INTO courses_course (title, description, instructor_id, category_id, level, price, is_published) VALUES
('Python для начинающих', 'Полный курс по основам программирования на Python для начинающих', 2, 1, 'beginner', 0.00, TRUE),
('Веб-разработка на Django', 'Создание веб-приложений с использованием фреймворка Django', 2, 1, 'intermediate', 4999.00, TRUE),
('UI/UX дизайн основы', 'Основы пользовательского интерфейса и пользовательского опыта', 3, 2, 'beginner', 2999.00, TRUE),
('Цифровой маркетинг', 'Продвижение в социальных сетях и поисковых системах', 2, 3, 'beginner', 3999.00, TRUE),
('Бизнес-планирование', 'Создание и анализ бизнес-планов для стартапов', 3, 4, 'intermediate', 5999.00, TRUE);

INSERT INTO courses_lesson (title, course_id, content, "order", is_free) VALUES
('Введение в Python', 1, 'Python - это высокоуровневый язык программирования...', 1, TRUE),
('Переменные и типы данных', 1, 'В Python есть несколько встроенных типов данных...', 2, TRUE),
('Условные операторы', 1, 'Условные операторы позволяют выполнять разный код...', 3, FALSE),
('Циклы в Python', 1, 'Циклы используются для многократного выполнения кода...', 4, FALSE),
('Функции', 1, 'Функции - это блоки кода, которые можно вызывать...', 5, FALSE),
('Введение в Django', 2, 'Django - это фреймворк для веб-разработки...', 1, TRUE),
('Настройка проекта', 2, 'Создание и настройка нового Django проекта...', 2, FALSE),
('Модели и базы данных', 2, 'Работа с моделями Django и базами данных...', 3, FALSE);

INSERT INTO courses_courseenrollment (user_id, course_id, progress) VALUES
(4, 1, 75),
(4, 2, 30),
(5, 1, 100),
(5, 3, 45),
(6, 1, 20),
(6, 4, 10);

INSERT INTO courses_courselike (user_id, course_id) VALUES
(4, 1),
(4, 2),
(5, 1),
(5, 3),
(6, 1),
(6, 4);

INSERT INTO courses_coursereview (user_id, course_id, rating, comment) VALUES
(4, 1, 5, 'Отличный курс! Все понятно объяснено.'),
(5, 1, 4, 'Хороший курс, но могло быть больше практических заданий.'),
(5, 3, 5, 'Очень понравился курс по дизайну. Рекомендую!'),
(6, 1, 4, 'Python оказался интереснее, чем я думал.');

INSERT INTO chat_supportchat (user_id, subject, status) VALUES
(4, 'Вопрос по курсу Python', 'closed'),
(5, 'Проблема с доступом к урокам', 'in_progress'),
(6, 'Предложение по новому курсу', 'open');

INSERT INTO chat_message (chat_id, sender_id, content, is_read) VALUES
(1, 4, 'Здравствуйте! У меня вопрос по третьему уроку.', TRUE),
(1, 2, 'Здравствуйте! Задавайте ваш вопрос.', TRUE),
(1, 4, 'Не могу понять, как работают циклы for.', TRUE),
(1, 2, 'Цикл for используется для итерации по последовательностям...', TRUE),
(2, 5, 'Не могу открыть уроки 3 и 4 в курсе Django.', FALSE),
(2, 2, 'Проверим вашу подписку и доступы.', FALSE),
(3, 6, 'Добавьте пожалуйста курс по машинному обучению!', FALSE);

INSERT INTO adminpanel_activitylog (user_id, action_type, object_type, object_id, object_repr, details) VALUES
(4, 'login', 'user', 4, 'student1', '{"ip": "127.0.0.1", "user_agent": "Mozilla/5.0"}'),
(4, 'enroll_course', 'course', 1, 'Python для начинающих', '{"course_id": 1}'),
(4, 'complete_lesson', 'lesson', 1, 'Введение в Python', '{"lesson_id": 1}'),
(5, 'login', 'user', 5, 'student2', '{"ip": "127.0.0.1", "user_agent": "Mozilla/5.0"}'),
(5, 'submit_review', 'course', 1, 'Python для начинающих', '{"rating": 4}');

INSERT INTO adminpanel_systemlog (level, message, module, function, extra_data) VALUES
('INFO', 'Пользователь student1 вошел в систему', 'auth', 'login', '{"user_id": 4}'),
('INFO', 'Создан новый отзыв на курс', 'courses', 'submit_review', '{"course_id": 1, "rating": 4}'),
('WARNING', 'Попытка доступа к неопубликованному курсу', 'courses', 'course_detail', '{"course_id": 99}'),
('ERROR', 'Ошибка при загрузке урока', 'courses', 'lesson_view', '{"lesson_id": 999}');

INSERT INTO adminpanel_errorlog (error_type, message, url, method, resolved) VALUES
('404', 'Страница не найдена', '/courses/999/', 'GET', TRUE),
('500', 'Внутренняя ошибка сервера', '/api/enroll/', 'POST', FALSE),
('403', 'Доступ запрещен', '/adminpanel/', 'GET', TRUE);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_accounts_user_updated_at BEFORE UPDATE ON accounts_user FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_courses_course_updated_at BEFORE UPDATE ON courses_course FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chat_supportchat_updated_at BEFORE UPDATE ON chat_supportchat FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE FUNCTION get_user_stats(user_id_param INTEGER)
RETURNS TABLE(
    courses_enrolled INTEGER,
    courses_completed INTEGER,
    total_hours DECIMAL,
    average_rating DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT ce.course_id) as courses_enrolled,
        COUNT(DISTINCT CASE WHEN ce.progress = 100 THEN ce.course_id END) as courses_completed,
        COALESCE(SUM(ce.progress) * 0.5, 0) as total_hours,
        COALESCE(AVG(cr.rating), 0) as average_rating
    FROM courses_courseenrollment ce
    LEFT JOIN courses_coursereview cr ON ce.user_id = cr.user_id
    WHERE ce.user_id = user_id_param;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_course_stats(course_id_param INTEGER)
RETURNS TABLE(
    enrollment_count INTEGER,
    completion_rate DECIMAL,
    average_rating DECIMAL,
    total_revenue DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as enrollment_count,
        AVG(CASE WHEN ce.progress = 100 THEN 100 ELSE ce.progress END) as completion_rate,
        COALESCE(AVG(cr.rating), 0) as average_rating,
        COALESCE(SUM(c.price), 0) as total_revenue
    FROM courses_course c
    LEFT JOIN courses_courseenrollment ce ON c.id = ce.course_id
    LEFT JOIN courses_coursereview cr ON c.id = cr.course_id
    WHERE c.id = course_id_param
    GROUP BY c.id;
END;
$$ LANGUAGE plpgsql;

CREATE VIEW course_details AS
SELECT 
    c.id,
    c.title,
    c.description,
    c.level,
    c.price,
    c.is_published,
    c.created_at,
    cat.name as category_name,
    u.username as instructor_username,
    u.first_name as instructor_first_name,
    u.last_name as instructor_last_name,
    COUNT(DISTINCT ce.id) as enrollment_count,
    COALESCE(AVG(cr.rating), 0) as average_rating,
    COUNT(DISTINCT cr.id) as review_count,
    COUNT(DISTINCT l.id) as lesson_count
FROM courses_course c
LEFT JOIN courses_category cat ON c.category_id = cat.id
LEFT JOIN accounts_user u ON c.instructor_id = u.id
LEFT JOIN courses_courseenrollment ce ON c.id = ce.course_id
LEFT JOIN courses_coursereview cr ON c.id = cr.course_id
LEFT JOIN courses_lesson l ON c.id = l.course_id
GROUP BY c.id, cat.name, u.username, u.first_name, u.last_name;

CREATE VIEW user_activity_summary AS
SELECT 
    u.id,
    u.username,
    u.first_name,
    u.last_name,
    u.role,
    u.date_joined,
    COUNT(DISTINCT ce.course_id) as courses_enrolled,
    COUNT(DISTINCT CASE WHEN ce.progress = 100 THEN ce.course_id END) as courses_completed,
    COALESCE(AVG(cr.rating), 0) as average_rating_given,
    COUNT(DISTINCT cr.id) as reviews_count,
    COUNT(DISTINCT cl.id) as likes_count,
    COUNT(DISTINCT sc.id) as support_chats_count
FROM accounts_user u
LEFT JOIN courses_courseenrollment ce ON u.id = ce.user_id
LEFT JOIN courses_coursereview cr ON u.id = cr.user_id
LEFT JOIN courses_courselike cl ON u.id = cl.user_id
LEFT JOIN chat_supportchat sc ON u.id = sc.user_id
GROUP BY u.id, u.username, u.first_name, u.last_name, u.role, u.date_joined;

ALTER TABLE courses_courseenrollment ADD CONSTRAINT check_progress 
CHECK (progress >= 0 AND progress <= 100);

ALTER TABLE courses_coursereview ADD CONSTRAINT check_rating 
CHECK (rating >= 1 AND rating <= 5);

ALTER TABLE courses_course ADD CONSTRAINT check_price 
CHECK (price >= 0);

ALTER TABLE courses_lesson ADD CONSTRAINT check_order 
CHECK ("order" >= 0);

CREATE ROLE read_only;
CREATE ROLE read_write;
CREATE ROLE admin_role;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO read_only;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO read_write;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO read_write;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin_role;

ANALYZE;
VACUUM ANALYZE;
