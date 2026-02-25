#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.
Run: python manage.py runserver
"""

import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'leetcode_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
