import multiprocessing
import os


bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

default_workers = min(max(2, multiprocessing.cpu_count() * 2 + 1), 4)
workers = int(os.environ.get("GUNICORN_WORKERS", str(default_workers)))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))

timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")

accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "-")
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "-")
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
capture_output = True

max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "100"))
