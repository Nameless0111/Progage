-- ERD-модель базы данных для системы управления учебными ресурсами
-- PostgreSQL Workbench compatible SQL

-- Создание базы данных
-- CREATE DATABASE resource_management;
-- \c resource_management;

-- Удаление существующих таблиц (для пересоздания)
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS schedules CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS requests CASCADE;
DROP TABLE IF EXISTS resources CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS classrooms CASCADE;
DROP TABLE IF EXISTS resource_types CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Создание перечислений (enums)
CREATE TYPE user_role AS ENUM ('admin', 'teacher', 'technician', 'student');
CREATE TYPE resource_type_enum AS ENUM ('projector', 'laptop', 'printer', 'textbook', 'lab_equipment', 'other');
CREATE TYPE classroom_type AS ENUM ('lecture', 'lab', 'computer', 'workshop');
CREATE TYPE course_type AS ENUM ('lecture', 'practical', 'laboratory');
CREATE TYPE request_status AS ENUM ('new', 'in_progress', 'waiting', 'closed');
CREATE TYPE request_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE notification_type AS ENUM ('status_change', 'new_assign', 'delay', 'new_request', 'resource_available');

-- Таблица пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role user_role NOT NULL DEFAULT 'student',
    date_joined TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    phone VARCHAR(20),
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица типов учебных ресурсов
CREATE TABLE resource_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица учебных кабинетов
CREATE TABLE classrooms (
    id SERIAL PRIMARY KEY,
    number VARCHAR(10) NOT NULL,
    type classroom_type NOT NULL,
    capacity INTEGER,
    building_id INTEGER NOT NULL DEFAULT 1,
    floor INTEGER DEFAULT 1,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица учебных курсов
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type course_type NOT NULL,
    max_students INTEGER,
    teacher_id INTEGER NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- Таблица учебных ресурсов
CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    serial_number VARCHAR(30) UNIQUE,
    resource_type_id INTEGER NOT NULL,
    brand VARCHAR(100),
    model VARCHAR(100),
    description TEXT,
    classroom_id INTEGER,
    teacher_id INTEGER,
    purchase_date DATE,
    warranty_until DATE,
    status VARCHAR(20) DEFAULT 'available',
    is_available BOOLEAN DEFAULT TRUE,
    cost DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_type_id) REFERENCES resource_types(id) ON DELETE RESTRICT,
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE SET NULL,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Таблица заявок на обслуживание
CREATE TABLE requests (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    status request_status NOT NULL DEFAULT 'new',
    priority request_priority NOT NULL DEFAULT 'medium',
    resource_id INTEGER,
    requester_id INTEGER NOT NULL,
    assigned_tech_id INTEGER,
    create_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    close_date TIMESTAMP WITH TIME ZONE,
    result TEXT,
    estimated_hours DECIMAL(4,2),
    actual_hours DECIMAL(4,2),
    cost DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE SET NULL,
    FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (assigned_tech_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Таблица уведомлений
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    notification_type notification_type NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    create_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_date TIMESTAMP WITH TIME ZONE,
    related_request_id INTEGER,
    related_resource_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (related_request_id) REFERENCES requests(id) ON DELETE SET NULL,
    FOREIGN KEY (related_resource_id) REFERENCES resources(id) ON DELETE SET NULL
);

-- Таблица расписания занятий
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL,
    classroom_id INTEGER NOT NULL,
    resource_id INTEGER,
    schedule_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    title VARCHAR(100),
    description TEXT,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurring_pattern VARCHAR(50),
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE RESTRICT,
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE SET NULL
);

-- Таблица аудита (лог операций)
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    object_id INTEGER NOT NULL,
    old_values TEXT,
    new_values TEXT,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- Создание индексов для оптимизации запросов
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_resources_name ON resources(name);
CREATE INDEX idx_resources_serial_number ON resources(serial_number);
CREATE INDEX idx_resources_type_id ON resources(resource_type_id);
CREATE INDEX idx_resources_classroom_id ON resources(classroom_id);
CREATE INDEX idx_resources_teacher_id ON resources(teacher_id);
CREATE INDEX idx_resources_is_available ON resources(is_available);
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_priority ON requests(priority);
CREATE INDEX idx_requests_requester_id ON requests(requester_id);
CREATE INDEX idx_requests_assigned_tech_id ON requests(assigned_tech_id);
CREATE INDEX idx_requests_create_date ON requests(create_date);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_create_date ON notifications(create_date);
CREATE INDEX idx_schedules_course_id ON schedules(course_id);
CREATE INDEX idx_schedules_classroom_id ON schedules(classroom_id);
CREATE INDEX idx_schedules_resource_id ON schedules(resource_id);
CREATE INDEX idx_schedules_date ON schedules(schedule_date);
CREATE INDEX idx_schedules_time_range ON schedules(start_time, end_time);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_model_name ON audit_log(model_name);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);

-- Создание триггеров для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Применение триггеров к таблицам
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resource_types_updated_at BEFORE UPDATE ON resource_types
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_classrooms_updated_at BEFORE UPDATE ON classrooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_requests_updated_at BEFORE UPDATE ON requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Создание триггера для аудита
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (user_id, action, model_name, object_id, new_values)
        VALUES (COALESCE(NEW.created_by, 1), 'INSERT', TG_TABLE_NAME, NEW.id, 
                row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (user_id, action, model_name, object_id, old_values, new_values)
        VALUES (COALESCE(NEW.updated_by, 1), 'UPDATE', TG_TABLE_NAME, NEW.id,
                row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (user_id, action, model_name, object_id, old_values)
        VALUES (COALESCE(OLD.updated_by, 1), 'DELETE', TG_TABLE_NAME, OLD.id,
                row_to_json(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Применение триггера аудита (раскомментировать при необходимости)
-- CREATE TRIGGER audit_resources_trigger
--     AFTER INSERT OR UPDATE OR DELETE ON resources
--     FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Вставка начальных данных
-- Типы ресурсов
INSERT INTO resource_types (name, description) VALUES
('Проектор', 'Мультимедийные проекторы для презентаций'),
('Ноутбук', 'Портативные компьютеры для преподавателей'),
('Принтер', 'Устройства печати документов'),
('Учебник', 'Печатные учебные пособия'),
('Лабораторное оборудование', 'Оборудование для практических занятий'),
('Другое', 'Прочие учебные ресурсы');

-- Кабинеты
INSERT INTO classrooms (number, type, capacity, building_id, floor) VALUES
('101', 'lecture', 50, 1, 1),
('102', 'lecture', 40, 1, 1),
('201', 'lab', 25, 1, 2),
('202', 'computer', 30, 1, 2),
('301', 'workshop', 20, 1, 3);

-- Администратор по умолчанию
INSERT INTO users (username, email, password, first_name, last_name, role) VALUES
('admin', 'admin@example.com', 'pbkdf2_sha256$...', 'Администратор', 'Системы', 'admin');

-- Преподаватели
INSERT INTO users (username, email, password, first_name, last_name, role) VALUES
('teacher1', 'teacher1@example.com', 'pbkdf2_sha256$...', 'Иван', 'Петров', 'teacher'),
('teacher2', 'teacher2@example.com', 'pbkdf2_sha256$...', 'Мария', 'Сидорова', 'teacher');

-- Технические специалисты
INSERT INTO users (username, email, password, first_name, last_name, role) VALUES
('tech1', 'tech1@example.com', 'pbkdf2_sha256$...', 'Алексей', 'Кузнецов', 'technician'),
('tech2', 'tech2@example.com', 'pbkdf2_sha256$...', 'Елена', 'Смирнова', 'technician');

-- Студенты
INSERT INTO users (username, email, password, first_name, last_name, role) VALUES
('student1', 'student1@example.com', 'pbkdf2_sha256$...', 'Анна', 'Иванова', 'student'),
('student2', 'student2@example.com', 'pbkdf2_sha256$...', 'Петр', 'Васильев', 'student');

-- Примеры ресурсов
INSERT INTO resources (name, serial_number, resource_type_id, brand, model, classroom_id, teacher_id, is_available) VALUES
('Проектор Epson', 'EP123456789', 1, 'Epson', 'EB-X41', 1, 2, TRUE),
('Ноутбук Dell', 'DL987654321', 2, 'Dell', 'Latitude 5420', 2, 1, TRUE),
('Принтер HP', 'HP456789123', 3, 'HP', 'LaserJet Pro M404n', 3, NULL, TRUE);

-- Комментарии для Workbench
/*
ERD Relationships:
1. Users (1:N) -> Resources (teacher_id)
2. Users (1:N) -> Courses (teacher_id)
3. Users (1:N) -> Requests (requester_id)
4. Users (1:N) -> Requests (assigned_tech_id)
5. Users (1:N) -> Notifications (user_id)
6. Users (1:N) -> AuditLog (user_id)
7. ResourceTypes (1:N) -> Resources (resource_type_id)
8. Classrooms (1:N) -> Resources (classroom_id)
9. Classrooms (1:N) -> Schedules (classroom_id)
10. Courses (1:N) -> Schedules (course_id)
11. Resources (1:N) -> Requests (resource_id)
12. Resources (1:N) -> Schedules (resource_id)
13. Requests (1:N) -> Notifications (related_request_id)
14. Resources (1:N) -> Notifications (related_resource_id)

Index Strategy:
- Foreign keys for JOIN performance
- Status fields for filtering
- Date/time fields for range queries
- Search fields for text search
- Composite indexes for common query patterns

Constraints:
- NOT NULL for required fields
- UNIQUE for natural keys
- FOREIGN KEY for referential integrity
- CHECK for data validation
- DEFAULT values for consistency

Performance Considerations:
- Partitioning for large tables (audit_log)
- Proper indexing strategy
- Query optimization
- Connection pooling
- Caching layer

Security:
- Row Level Security (RLS) for multi-tenancy
- Proper user permissions
- Audit trail for compliance
- Data encryption at rest
- Secure password hashing
*/
