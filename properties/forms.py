"""
Real Estate DBMS - Django Forms (NO ORM)
All forms use plain Django fields, no ModelForm
"""

from django import forms
from datetime import datetime
from . import db_utils


# =====================================================
# PROFILE FORMS
# =====================================================

class ClientProfileForm(forms.Form):
    """Client profile form - NO ORM"""
    preferred_contact_method = forms.ChoiceField(
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('text', 'Text'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    budget_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum Budget'})
    )
    budget_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maximum Budget'})
    )
    preferred_location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Boston, MA'})
    )
    looking_for = forms.ChoiceField(
        choices=[
            ('buy', 'Buy'),
            ('rent', 'Rent'),
            ('sell', 'Sell'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class AgentProfileForm(forms.Form):
    """Agent profile form - NO ORM"""
    license_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    agency_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    commission_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=3.00,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    specialization = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Residential'})
    )
    years_experience = forms.IntegerField(
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


# =====================================================
# PROPERTY FORM
# =====================================================

class PropertyForm(forms.Form):
    """Property form - NO ORM, loads property types from database"""
    
    property_type = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Location
    street_address = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    zip_code = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Basic info
    title = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    price = forms.DecimalField(max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    listing_type = forms.ChoiceField(
        choices=[('sale', 'For Sale'), ('rent', 'For Rent')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    bedrooms = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    bathrooms = forms.DecimalField(max_digits=3, decimal_places=1, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}))
    square_feet = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    lot_size = forms.DecimalField(required=False, max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    year_built = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    parking_spaces = forms.IntegerField(initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    has_garage = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    has_pool = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    has_garden = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    listed_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    status = forms.ChoiceField(
        choices=[
            ('available', 'Available'),
            ('pending', 'Pending'),
            ('sold', 'Sold'),
            ('rented', 'Rented'),
            ('off_market', 'Off Market'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load property types using raw SQL
        property_types = db_utils.get_all_property_types()
        self.fields['property_type'].choices = [
            (str(pt['property_type_id']), pt['type_name']) for pt in property_types
        ]


class PropertySearchForm(forms.Form):
    """Property search form - NO ORM"""
    search_query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, city...'
        })
    )
    
    listing_type = forms.ChoiceField(
        choices=[('', 'Any'), ('sale', 'For Sale'), ('rent', 'For Rent')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    property_type = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Price'})
    )
    
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Price'})
    )
    
    min_bedrooms = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Bedrooms'})
    )
    
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'})
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Any Status'),
            ('available', 'Available'),
            ('pending', 'Pending'),
            ('sold', 'Sold'),
            ('rented', 'Rented')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load property types using raw SQL
        property_types = db_utils.get_all_property_types()
        self.fields['property_type'].choices = [('', 'Any Type')] + [
            (str(pt['property_type_id']), pt['type_name']) for pt in property_types
        ]


# =====================================================
# APPOINTMENT FORMS
# =====================================================

class AppointmentForm(forms.Form):
    """Appointment form - NO ORM"""
    appointment_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    duration_minutes = forms.IntegerField(
        initial=60,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'value': 60})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class AppointmentUpdateForm(forms.Form):
    """Appointment update form - NO ORM"""
    status = forms.ChoiceField(
        choices=[
            ('scheduled', 'Scheduled'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('no_show', 'No Show'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


# =====================================================
# TRANSACTION FORM
# =====================================================

class TransactionForm(forms.Form):
    """Transaction form - NO ORM"""
    transaction_type = forms.ChoiceField(
        choices=[
            ('sale', 'Sale'),
            ('rental', 'Rental'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    transaction_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    final_price = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    payment_status = forms.ChoiceField(
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        initial='completed',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    lease_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    lease_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


# =====================================================
# REVIEW FORM
# =====================================================

class ReviewForm(forms.Form):
    """Review form - NO ORM"""
    rating = forms.ChoiceField(
        choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    review_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Share your experience...'
        })
    )