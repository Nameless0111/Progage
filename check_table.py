import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_name = \'accounts_notification\' ORDER BY ordinal_position')
columns = [row[0] for row in cursor.fetchall()]
print("Table columns:", columns)
