"""
Authentication Utilities - 100% Raw SQL, NO ORM
Uses pure Python for password hashing
"""

import hashlib
import os
import binascii
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from . import db_utils


# =====================================================
# PASSWORD HASHING (Pure Python - NO Django)
# =====================================================

def hash_password(password):
    """
    Hash password using PBKDF2-SHA256
    Pure Python standard library - NO Django, NO ORM
    """
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')


def verify_password(stored_password, provided_password):
    """
    Verify a stored password against provided password
    Pure Python - NO Django, NO ORM
    """
    salt = stored_password[:64]
    stored_password_hash = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password_hash


# =====================================================
# USER AUTHENTICATION (Raw SQL)
# =====================================================

def create_user(email, password, first_name, last_name, phone, user_type):
    """
    Create a new user - Raw SQL only
    Returns: user_id
    """
    password_hash = hash_password(password)
    
    query = """
        INSERT INTO Users (
            email, username, password_hash, first_name, last_name, phone,
            user_type, is_active, is_superuser, is_staff, created_at, updated_at, date_joined
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, FALSE, FALSE, NOW(), NOW(), NOW())
    """
    
    return db_utils.execute_insert(query, (email, email, password_hash, first_name, last_name, phone, user_type))


def authenticate_user(email, password):
    """
    Authenticate user - Raw SQL only
    Returns: User dictionary if authenticated, None otherwise
    """
    query = """
        SELECT user_id, email, username, password_hash, first_name, last_name,
               phone, user_type, is_active, is_superuser, is_staff
        FROM Users
        WHERE email = %s AND is_active = TRUE
    """
    
    results = db_utils.execute_query(query, (email,))
    
    if not results:
        return None
    
    user = results[0]
    
    # Verify password
    if verify_password(user['password_hash'], password):
        # Update last_login
        update_query = "UPDATE Users SET last_login = NOW() WHERE user_id = %s"
        db_utils.execute_update(update_query, (user['user_id'],))
        
        return user
    
    return None


def get_user_by_id(user_id):
    """Get user by ID - Raw SQL"""
    query = """
        SELECT user_id, email, username, first_name, last_name, phone,
               user_type, is_active, is_superuser, is_staff
        FROM Users
        WHERE user_id = %s
    """
    results = db_utils.execute_query(query, (user_id,))
    return results[0] if results else None


def check_user_exists(email):
    """Check if user exists - Raw SQL"""
    query = "SELECT COUNT(*) as count FROM Users WHERE email = %s"
    result = db_utils.execute_query(query, (email,))
    return result[0]['count'] > 0


# =====================================================
# CUSTOM LOGIN DECORATOR (No ORM)
# =====================================================

def login_required_custom(view_func):
    """
    Custom login required decorator
    Uses session only - NO database queries, NO ORM
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# =====================================================
# SIMPLE USER CLASS (No ORM)
# =====================================================

class SimpleUser:
    """
    Simple user object from session data
    NO database queries, NO ORM
    """
    def __init__(self, session_data):
        self.user_id = session_data.get('user_id')
        self.email = session_data.get('email')
        self.first_name = session_data.get('first_name', '')
        self.last_name = session_data.get('last_name', '')
        self.user_type = session_data.get('user_type', '')
        self.is_authenticated = session_data.get('is_authenticated', False)
    
    def __bool__(self):
        return self.is_authenticated
    
    def __str__(self):
        if self.is_authenticated:
            return f"{self.first_name} {self.last_name}"
        return "AnonymousUser"
