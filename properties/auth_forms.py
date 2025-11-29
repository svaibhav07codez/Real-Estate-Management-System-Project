"""
Authentication Forms - NO ORM
Pure Django forms without ModelForm
"""

from django import forms
from django.core.validators import EmailValidator
import re
from . import auth_utils


class RegistrationForm(forms.Form):
    """User registration form - NO ORM"""
    
    email = forms.EmailField(
        required=True,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )
    
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John'
        })
    )
    
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Doe'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '555-1234'
        })
    )
    
    user_type = forms.ChoiceField(
        choices=[
            ('client', 'Client (Looking to buy/rent)'),
            ('agent', 'Agent (Real estate professional)')
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    password1 = forms.CharField(
        label='Password',
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        }),
        help_text='Must be at least 6 characters'
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    def clean_email(self):
        """Validate email is unique"""
        email = self.cleaned_data.get('email')
        if email:
            if auth_utils.check_user_exists(email):
                raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def clean(self):
        """Validate passwords match"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data


class LoginForm(forms.Form):
    """Login form - NO ORM"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
