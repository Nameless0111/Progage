#!/usr/bin/env python
"""Django's command-line utility for administrative tasks on shared hosting."""
import os
import sys

if __name__ == '__main__':
    # Set settings module for shared hosting
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.shared_hosting')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
