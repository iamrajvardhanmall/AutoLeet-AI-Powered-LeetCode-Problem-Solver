"""
WSGI config for leetcode_project.
Used by Django's built-in server.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'leetcode_project.settings')
application = get_wsgi_application()
