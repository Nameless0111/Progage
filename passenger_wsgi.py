#!/usr/bin/env python
"""
Passenger WSGI configuration for shared hosting
"""
import os
import sys

# Add the project directory to Python path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)
sys.path.insert(0, os.path.join(project_path, 'progage'))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.shared_hosting')

# Import Django
import django
django.setup()

# Import WSGI application
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
