# ДИАГРАММЫ СИСТЕМЫ УПРАВЛЕНИЯ УЧЕБНЫМИ РЕСУРСАМИ

## Рисунок 1 – Диаграмма прецедентов (Use Case Diagram)

```mermaid
graph TD
    A[Система управления учебными ресурсами] --> B[Администратор]
    A --> C[Преподаватель]
    A --> D[Технический специалист]
    A --> E[Студент]
    
    %% Администраторские функции
    B --> F1[Управление пользователями]
    B --> F2[Управление ресурсами]
    B --> F3[Управление кабинетами]
    B --> F4[Просмотр отчетов]
    B --> F5[Резервное копирование]
    B --> F6[Просмотр логов]
    
    %% Функции преподавателя
    C --> F7[Просмотр доступных ресурсов]
    C --> F8[Создание заявок на обслуживание]
    C --> F9[Бронирование ресурсов]
    C --> F10[Просмотр своих заявок]
    C --> F11[Управление курсами]
    C --> F12[Просмотр расписания]
    
    %% Функции технического специалиста
    D --> F13[Обработка заявок]
    D --> F14[Регистрация перемещений]
    D --> F15[Фиксация ремонтов]
    D --> F16[Просмотр нагрузки]
    D --> F17[Управление статусами]
    
    %% Функции студента
    E --> F18[Просмотр доступных ресурсов]
    E --> F19[Просмотр расписания]
    E --> F20[Поиск учебных материалов]
    
    %% Общие функции
    A --> G1[Авторизация]
    A --> G2[Просмотр уведомлений]
    A --> G3[Чат поддержки]
    A --> G4[Поиск ресурсов]
    
    %% Связи между функциями
    F8 --> F13
    F9 --> F7
    F10 --> F2
    F15 --> F4
    F17 --> F10
```

## Рисунок 2 – Функциональная схема

```mermaid
graph TB
    subgraph "Пользовательский интерфейс"
        UI1[Веб-интерфейс]
        UI2[Мобильный интерфейс]
    end
    
    subgraph "Контроллеры (Views)"
        V1[AccountController]
        V2[ResourceController]
        V3[RequestController]
        V4[ScheduleController]
        V5[ReportController]
        V6[NotificationController]
    end
    
    subgraph "Модели данных"
        M1[User Model]
        M2[Resource Model]
        M3[Request Model]
        M4[Schedule Model]
        M5[Classroom Model]
        M6[Course Model]
        M7[Notification Model]
    end
    
    subgraph "Бизнес-логика"
        BL1[Управление доступом]
        BL2[Валидация данных]
        BL3[Уведомления]
        BL4[Формирование отчетов]
        BL5[Резервное копирование]
    end
    
    subgraph "Уровень данных"
        DB[(PostgreSQL)]
        CACHE[(Redis Cache)]
        FILES[(Файловое хранилище)]
    end
    
    subgraph "Внешние сервисы"
        EMAIL[Email сервис]
        SMS[SMS сервис]
        BACKUP[Сервис бэкапов]
    end
    
    %% Связи
    UI1 --> V1
    UI1 --> V2
    UI1 --> V3
    UI1 --> V4
    UI1 --> V5
    UI1 --> V6
    
    UI2 --> V1
    UI2 --> V2
    UI2 --> V3
    
    V1 --> M1
    V1 --> BL1
    V2 --> M2
    V2 --> M5
    V2 --> BL2
    V3 --> M3
    V3 --> BL3
    V4 --> M4
    V4 --> M6
    V5 --> BL4
    V6 --> M7
    V6 --> BL3
    
    BL1 --> DB
    BL2 --> DB
    BL3 --> EMAIL
    BL3 --> SMS
    BL4 --> DB
    BL5 --> BACKUP
    
    M1 --> DB
    M2 --> DB
    M3 --> DB
    M4 --> DB
    M5 --> DB
    M6 --> DB
    M7 --> DB
    
    V1 --> CACHE
    V2 --> CACHE
    V3 --> CACHE
    
    V5 --> FILES
    BL5 --> FILES
```

## Рисунок 7 – ERD-модель базы данных

```mermaid
erDiagram
    USERS {
        int id PK
        varchar username
        varchar email
        varchar password
        varchar first_name
        varchar last_name
        enum role
        datetime date_joined
        boolean is_active
    }
    
    RESOURCE_TYPES {
        int id PK
        varchar name
        text description
    }
    
    RESOURCES {
        int id PK
        varchar name
        varchar serial_number
        int resource_type_id FK
        varchar brand
        varchar model
        text description
        int classroom_id FK
        int teacher_id FK
        datetime create_date
        boolean is_available
    }
    
    CLASSROOMS {
        int id PK
        varchar number
        enum type
        int capacity
        int building_id
    }
    
    COURSES {
        int id PK
        varchar name
        enum type
        int max_students
        int teacher_id FK
    }
    
    REQUESTS {
        int id PK
        varchar title
        text description
        enum status
        enum priority
        int resource_id FK
        int requester_id FK
        int assigned_tech_id FK
        datetime create_date
        datetime close_date
        text result
    }
    
    NOTIFICATIONS {
        int id PK
        int user_id FK
        enum notification_type
        varchar title
        text message
        boolean is_read
        datetime create_date
    }
    
    SCHEDULES {
        int id PK
        int course_id FK
        int classroom_id FK
        int resource_id FK
        date schedule_date
        time start_time
        time end_time
    }
    
    AUDIT_LOG {
        int id PK
        int user_id FK
        varchar action
        varchar model_name
        int object_id
        text old_values
        text new_values
        datetime timestamp
    }
    
    %% Связи
    USERS ||--o{ RESOURCES : "teacher_id"
    USERS ||--o{ COURSES : "teacher_id"
    USERS ||--o{ REQUESTS : "requester_id"
    USERS ||--o{ REQUESTS : "assigned_tech_id"
    USERS ||--o{ NOTIFICATIONS : "user_id"
    USERS ||--o{ AUDIT_LOG : "user_id"
    
    RESOURCE_TYPES ||--o{ RESOURCES : "resource_type_id"
    
    CLASSROOMS ||--o{ RESOURCES : "classroom_id"
    CLASSROOMS ||--o{ SCHEDULES : "classroom_id"
    
    COURSES ||--o{ SCHEDULES : "course_id"
    
    RESOURCES ||--o{ REQUESTS : "resource_id"
    RESOURCES ||--o{ SCHEDULES : "resource_id"
```

## Рисунок 8 – Схема пользовательского интерфейса

```mermaid
graph TB
    subgraph "Главный экран"
        MAIN[Главная страница]
        NAV[Навигационная панель]
        SEARCH[Поиск ресурсов]
        NOTIF[Центр уведомлений]
    end
    
    subgraph "Разделы системы"
        RESOURCES[Управление ресурсами]
        REQUESTS[Заявки на обслуживание]
        SCHEDULES[Расписание занятий]
        REPORTS[Отчеты и аналитика]
        USERS[Управление пользователями]
        SETTINGS[Настройки]
    end
    
    subgraph "Страницы ресурсов"
        RES_LIST[Список ресурсов]
        RES_DETAIL[Детали ресурса]
        RES_ADD[Добавление ресурса]
        RES_EDIT[Редактирование ресурса]
    end
    
    subgraph "Страницы заявок"
        REQ_LIST[Список заявок]
        REQ_DETAIL[Детали заявки]
        REQ_ADD[Создание заявки]
        REQ_EDIT[Редактирование заявки]
    end
    
    subgraph "Страницы расписания"
        SCHED_LIST[Список занятий]
        SCHED_DETAIL[Детали занятия]
        SCHED_ADD[Добавление занятия]
        SCHED_CALENDAR[Календарь]
    end
    
    subgraph "Страницы отчетов"
        REP_STATS[Статистика]
        REP_ANALYTICS[Аналитика]
        REP_EXPORT[Экспорт данных]
        REP_HISTORY[История изменений]
    end
    
    subgraph "Личные кабинеты"
        ADMIN_PANEL[Панель администратора]
        TEACHER_PANEL[Панель преподавателя]
        TECH_PANEL[Панель техника]
        STUDENT_PANEL[Панель студента]
    end
    
    subgraph "Модальные окна"
        MODAL_CONFIRM[Подтверждение]
        MODAL_ALERT[Предупреждение]
        MODAL_FORM[Форма ввода]
        MODAL_SUCCESS[Успешное выполнение]
    end
    
    %% Навигация
    MAIN --> NAV
    NAV --> RESOURCES
    NAV --> REQUESTS
    NAV --> SCHEDULES
    NAV --> REPORTS
    NAV --> USERS
    NAV --> SETTINGS
    
    RESOURCES --> RES_LIST
    RES_LIST --> RES_DETAIL
    RES_LIST --> RES_ADD
    RES_DETAIL --> RES_EDIT
    
    REQUESTS --> REQ_LIST
    REQ_LIST --> REQ_DETAIL
    REQ_LIST --> REQ_ADD
    REQ_DETAIL --> REQ_EDIT
    
    SCHEDULES --> SCHED_LIST
    SCHED_LIST --> SCHED_DETAIL
    SCHED_LIST --> SCHED_ADD
    SCHED_LIST --> SCHED_CALENDAR
    
    REPORTS --> REP_STATS
    REPORTS --> REP_ANALYTICS
    REPORTS --> REP_EXPORT
    REPORTS --> REP_HISTORY
    
    USERS --> ADMIN_PANEL
    USERS --> TEACHER_PANEL
    USERS --> TECH_PANEL
    USERS --> STUDENT_PANEL
    
    %% Модальные окна
    RES_ADD --> MODAL_FORM
    RES_EDIT --> MODAL_FORM
    REQ_ADD --> MODAL_FORM
    REQ_EDIT --> MODAL_FORM
    SCHED_ADD --> MODAL_FORM
    
    RES_EDIT --> MODAL_CONFIRM
    REQ_EDIT --> MODAL_CONFIRM
    SCHED_EDIT --> MODAL_CONFIRM
    
    MODAL_FORM --> MODAL_SUCCESS
    MODAL_FORM --> MODAL_ALERT
```

## Описание диаграмм

### Диаграмма прецедентов
Показывает функциональные требования системы с точки зрения пользователей. Включает 4 типа пользователей (администратор, преподаватель, технический специалист, студент) и их основные действия в системе.

### Функциональная схема
Отображает архитектуру системы с разделением на пользовательский интерфейс, контроллеры, модели данных, бизнес-логику и уровень данных. Показывает взаимодействие между компонентами и внешними сервисами.

### ERD-модель базы данных
Представляет структуру базы данных с 9 основными таблицами и связями между ними. Включает пользователей, ресурсы, заявки, расписания, уведомления и логи операций.

### Схема пользовательского интерфейса
Описывает структуру пользовательского интерфейса, навигацию между разделами, основные страницы и модальные окна. Показывает логику взаимодействия пользователя с системой.
