# 🔥 Нагрузочное тестирование Progage

## 📋 Обзор

Инструменты для тестирования производительности сайта:
- **Встроенный скрипт:** `load_test.py` - асинхронный тестировщик
- **Внешние инструменты:** Apache Bench, JMeter, k6, Locust
- **Онлайн сервисы:** Loader.io, WebPageTest, GTmetrix

---

## 🚀 Использование встроенного скрипта

### Установка зависимостей
```bash
pip install aiohttp
```

### Запуск теста
```bash
python load_test.py
```

### Пример конфигурации
```
🌐 Enter base URL (default: http://localhost:8000): http://216.162.45.1:8000
👥 Concurrent users (default: 50): 100
📊 Total requests (default: 500): 1000
```

### Результаты теста
```
📊 LOAD TEST RESULTS
=====================================
📈 Total Requests: 1000
✅ Successful: 950 (95.0%)
❌ Failed: 50 (5.0%)

⏱️  Response Times:
   Average: 0.234s
   Median: 0.198s
   Min: 0.045s
   Max: 2.345s
   95th percentile: 0.456s

🚀 Requests per second: 125.50
💾 Results saved to: load_test_results_20260409_112745.json
```

---

## 📊 Метрики производительности

### 🎯 Целевые показатели
| Метрика | Цель | Отлично | Хорошо |
|---------|-------|---------|--------|
| Response time | <2s | <1s | <2s |
| Success rate | >99% | >99.5% | >99% |
| Throughput | >100 req/s | >200 req/s | >100 req/s |
| Concurrent users | 1000 | 5000 | 1000 |

### 📈 Интерпретация результатов
- **<1s:** Отличная производительность
- **1-2s:** Хорошая производительность  
- **>2s:** Нужно оптимизировать
- **>5s:** Критические проблемы

---

## 🛠️ Внешние инструменты

### Apache Bench (встроенный в Apache)
```bash
ab -n 1000 -c 50 http://216.162.45.1:8000/
```

### JMeter (GUI приложение)
1. Скачай JMeter с https://jmeter.apache.org/
2. Создай Thread Group
3. Настрой 1000 запросов, 50 потоков
4. Добавь HTTP Request Sampler
5. Запусти тест

### k6 (современный инструмент)
```bash
# Установка
npm install -g k6

# Тест скрипт (script.js)
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: 50,
  duration: '30s',
};

export default function () {
  let response = http.get('http://216.162.45.1:8000/');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time <500ms': (r) => r.timings.duration < 500,
  });
}
```

```bash
k6 run script.js
```

---

## 🌐 Онлайн сервисы

### Loader.io
1. Зайди на https://loader.io/
2. Введи URL сайта
3. Настрой 1000 пользователей, 10 минут
4. Запусти тест

### WebPageTest
1. Перейди на https://www.webpagetest.org/
2. Введи URL сайта
3. Выбери "Repeat View 9" для детального анализа
4. Анализируй результаты

---

## 📋 Чеклист производительности

### ✅ Перед тестированием
- [ ] Сервер запущен в production режиме
- [ ] База данных оптимизирована
- [ ] Статические файлы сжаты
- [ ] Кэширование включено
- [ ] Логирование отключено (для чистых результатов)

### 🧪 Во время тестирования
- [ ] Мониторь CPU сервера
- [ ] Мониторь использование памяти
- [ ] Следи за скоростью ответа
- [ ] Проверяй ошибки 4xx/5xx
- [ ] Фиксируй пики нагрузки

### 📊 После тестирования
- [ ] Проанализируй медленные запросы
- [ ] Оптимизируй БД запросы
- [ ] Настрой кэширование
- [ ] Добавь CDN для статики
- [ ] Настрой балансировку

---

## 🔧 Оптимизация производительности

### 🗄️ База данных
```python
# Индексы для частых запросов
class Course(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

# Оптимизация запросов
courses = Course.objects.select_related('instructor').prefetch_related('lessons')
```

### 🗂️ Статические файлы
```python
# Сжатие в nginx
gzip on;
gzip_types text/css application/javascript application/json;

# Кэширование
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 🧠 Кэширование Django
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Кэширование запросов
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 минут
def course_list(request):
    pass
```

---

## 📈 Мониторинг в реальном времени

### Django Debug Toolbar
```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

### Prometheus + Grafana
```yaml
# docker-compose.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 🎯 Рекомендации по нагрузке

### 🏃‍♂️ Легкая нагрузка (до 100 пользователей)
- Цель: Базовая функциональность
- Тест: 50 пользователей, 500 запросов
- Ожидание: <1s ответ, >99% успех

### 🏃‍♂️ Средняя нагрузка (100-1000 пользователей)
- Цель: Реальная эксплуатация  
- Тест: 500 пользователей, 5000 запросов
- Ожидание: <2s ответ, >98% успех

### 🏃‍♂️ Высокая нагрузка (1000+ пользователей)
- Цель: Пиковая нагрузка
- Тест: 2000 пользователей, 20000 запросов
- Ожидание: <3s ответ, >95% успех

---

## 🚨 Анализ проблем

### 🐌 Медленные запросы (>2s)
```python
# Логирование медленных запросов
if response.time > 2.0:
    logger.warning(f"Slow query: {request.path} took {response.time}s")
```

### 💾 Высокое использование памяти
```bash
# Мониторинг памяти
top -p $(pgrep -f "python.*manage.py")
```

### 🔄 Высокая нагрузка на CPU
```bash
# Мониторинг CPU
htop -p $(pgrep -f "python.*manage.py")
```

---

## 📚 Дополнительные ресурсы

- [Django Performance Optimization](https://docs.djangoproject.com/en/stable/topics/performance/)
- [k6 Documentation](https://k6.io/docs/)
- [JMeter User Guide](https://jmeter.apache.org/usermanual/index.html)
- [WebPageTest Documentation](https://www.webpagetest.org/documentation/)

---

*Создано: 9 апреля 2026*  
*Обновлено: при каждом изменении производительности*
