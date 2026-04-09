#!/usr/bin/env python
"""
Django CGI script for shared hosting deployment
"""
import os
import sys

# Add the project directory to Python path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)
sys.path.insert(0, os.path.join(project_path, 'progage'))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.shared_hosting')

# Import Django after setting up environment
import django
django.setup()

# Import CGI modules
from django.core.wsgi import get_wsgi_application
from wsgiref.handlers import CGIHandler

# Create WSGI application
application = get_wsgi_application()

# Run CGI handler
handler = CGIHandler()
handler.run(application)
