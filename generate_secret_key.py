#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility for generating SECRET_KEY for Django project.
Usage: python generate_secret_key.py
"""
import os
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project path for Django import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables before importing Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_project.settings')

try:
    from django.core.management.utils import get_random_secret_key
    
    secret_key = get_random_secret_key()
    
    print("=" * 70)
    print("Generated SECRET_KEY for Django:")
    print("=" * 70)
    print(f"\nSECRET_KEY={secret_key}\n")
    print("=" * 70)
    print("\nCopy this line to your .env file")
    print("=" * 70)
    
except ImportError:
    # If Django is not installed, use alternative method
    import secrets
    import string
    
    # Generate random string 50 characters long
    alphabet = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(50))
    
    print("=" * 70)
    print("Generated SECRET_KEY (without Django):")
    print("=" * 70)
    print(f"\nSECRET_KEY={secret_key}\n")
    print("=" * 70)
    print("\nCopy this line to your .env file")
    print("=" * 70)
    print("\nNote: For more secure key, install Django and use:")
    print('python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"')
    print("=" * 70)

