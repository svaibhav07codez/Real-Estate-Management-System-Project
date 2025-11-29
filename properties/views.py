"""
Real Estate DBMS - Django Views
100% Raw PyMySQL - NO ORM ANYWHERE
All database operations use raw SQL queries
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from datetime import datetime, date
from decimal import Decimal

from .forms import (
    ClientProfileForm, AgentProfileForm,
    PropertyForm, PropertySearchForm, AppointmentForm,
    TransactionForm, ReviewForm, AppointmentUpdateForm
)
from .auth_forms import RegistrationForm

# Import raw SQL utilities - NO ORM
from . import db_utils
from . import auth_utils
from .auth_utils import login_required_custom


# =====================================================
# AUTHENTICATION VIEWS (100% Raw SQL)
# =====================================================

def register_view(request):
    """User registration - Raw SQL only, NO ORM"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Create user using raw SQL
                user_id = auth_utils.create_user(
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password1'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    phone=form.cleaned_data.get('phone', ''),
                    user_type=form.cleaned_data['user_type']
                )
                
                # Get user data
                user_data = auth_utils.get_user_by_id(user_id)
                
                # Create session manually - NO ORM
                request.session['user_id'] = user_data['user_id']
                request.session['email'] = user_data['email']
                request.session['first_name'] = user_data['first_name']
                request.session['last_name'] = user_data['last_name']
                request.session['user_type'] = user_data['user_type']
                request.session['is_authenticated'] = True
                
                user_type = form.cleaned_data['user_type']
                
                if user_type == 'agent':
                    messages.success(request, 'Account created! Please complete your agent profile.')
                    return redirect('agent_profile_create')
                else:
                    messages.success(request, 'Account created! Please complete your profile.')
                    return redirect('client_profile_create')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """User login - Raw SQL only, NO ORM"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Authenticate using raw SQL
        user_data = auth_utils.authenticate_user(email, password)
        
        if user_data:
            # Create session manually - NO ORM
            request.session['user_id'] = user_data['user_id']
            request.session['email'] = user_data['email']
            request.session['first_name'] = user_data['first_name']
            request.session['last_name'] = user_data['last_name']
            request.session['user_type'] = user_data['user_type']
            request.session['is_authenticated'] = True
            
            messages.success(request, f'Welcome back, {user_data["first_name"]}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'registration/login.html')


def logout_view(request):
    """User logout - Clear session"""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


# =====================================================
# HOME AND DASHBOARD VIEWS (100% Raw SQL)
# =====================================================

def home_view(request):
    """Homepage - Raw SQL only"""
    # Get featured properties
    featured_properties = db_utils.get_all_properties({'status': 'available'})[:6]
    
    # Get images for each property
    for prop in featured_properties:
        images = db_utils.get_property_images(prop['property_id'])
        prop['images'] = images
        prop['primary_image'] = next((img for img in images if img['is_primary']), images[0] if images else None)
    
    # Get statistics
    stats_query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available
        FROM Properties
    """
    stats = db_utils.execute_query(stats_query)[0]
    
    agents_query = "SELECT COUNT(*) as total FROM Agents"
    agent_stats = db_utils.execute_query(agents_query)[0]
    
    context = {
        'featured_properties': featured_properties,
        'total_properties': stats['total'],
        'available_properties': stats['available'],
        'total_agents': agent_stats['total'],
    }
    return render(request, 'home.html', context)


@login_required_custom
def dashboard_view(request):
    """Dashboard router"""
    user_type = request.session.get('user_type')
    
    if user_type == 'admin':
        return redirect('admin_dashboard')
    elif user_type == 'agent':
        return redirect('agent_dashboard')
    else:
        return redirect('client_dashboard')


@login_required_custom
def client_dashboard(request):
    """Client dashboard - Raw SQL only"""
    user_id = request.session.get('user_id')
    client = db_utils.get_client_by_user_id(user_id)
    
    if not client:
        messages.warning(request, 'Please complete your profile.')
        return redirect('client_profile_create')
    
    # Get appointments
    appointments = db_utils.get_appointments_by_client(client['client_id'])[:5]
    
    # Get reviews
    reviews_query = """
        SELECT r.*, p.title as property_title
        FROM Reviews r
        LEFT JOIN Properties p ON r.property_id = p.property_id
        WHERE r.client_id = %s
        ORDER BY r.review_date DESC
        LIMIT 5
    """
    reviews = db_utils.execute_query(reviews_query, (client['client_id'],))
    
    # Get recommended properties
    filters = {'status': 'available'}
    if client.get('budget_min') and client.get('budget_max'):
        filters['min_price'] = client['budget_min']
        filters['max_price'] = client['budget_max']
    if client.get('preferred_location'):
        filters['city'] = client['preferred_location']
    
    recommended_properties = db_utils.get_all_properties(filters)[:6]
    
    # Add images
    for prop in recommended_properties:
        images = db_utils.get_property_images(prop['property_id'])
        prop['images'] = images
    
    context = {
        'client': client,
        'appointments': appointments,
        'reviews': reviews,
        'recommended_properties': recommended_properties,
    }
    return render(request, 'dashboard/client_dashboard.html', context)


@login_required_custom
def agent_dashboard(request):
    """Agent dashboard - Raw SQL only"""
    user_id = request.session.get('user_id')
    agent = db_utils.get_agent_by_user_id(user_id)
    
    if not agent:
        messages.warning(request, 'Please complete your agent profile.')
        return redirect('agent_profile_create')
    
    # Get agent's properties
    properties = db_utils.get_properties_by_agent(agent['agent_id'])
    active_listings = sum(1 for p in properties if p['status'] == 'available')
    
    # Get appointments
    appointments = db_utils.get_appointments_by_agent(agent['agent_id'])[:5]
    
    # Get transactions
    transactions = db_utils.get_transactions_by_agent(agent['agent_id'])[:5]
    
    # Get total commission
    total_commission = db_utils.get_agent_total_commission(agent['agent_id'])
    
    context = {
        'agent': agent,
        'properties': properties,
        'active_listings': active_listings,
        'appointments': appointments,
        'transactions': transactions,
        'total_commission': total_commission,
    }
    return render(request, 'dashboard/agent_dashboard.html', context)


@login_required_custom
def admin_dashboard(request):
    """Admin dashboard - Raw SQL only"""
    if request.session.get('user_type') != 'admin':
        return HttpResponseForbidden("Access denied")
    
    # Get statistics
    stats_query = """
        SELECT 
            (SELECT COUNT(*) FROM Properties) as total_properties,
            (SELECT COUNT(*) FROM Users) as total_users,
            (SELECT COUNT(*) FROM Agents) as total_agents,
            (SELECT COUNT(*) FROM Clients) as total_clients,
            (SELECT COUNT(*) FROM Transactions) as total_transactions,
            (SELECT COALESCE(SUM(final_price), 0) FROM Transactions WHERE payment_status = 'completed') as total_revenue
    """
    stats = db_utils.execute_query(stats_query)[0]
    
    # Recent properties
    recent_query = """
        SELECT p.*, l.city, l.state, u.first_name as agent_first_name, u.last_name as agent_last_name
        FROM Properties p
        JOIN Locations l ON p.location_id = l.location_id
        JOIN Agents a ON p.agent_id = a.agent_id
        JOIN Users u ON a.user_id = u.user_id
        ORDER BY p.created_at DESC
        LIMIT 5
    """
    recent_properties = db_utils.execute_query(recent_query)
    
    # Recent transactions
    trans_query = """
        SELECT t.*, p.title as property_title
        FROM Transactions t
        JOIN Properties p ON t.property_id = p.property_id
        ORDER BY t.transaction_date DESC
        LIMIT 5
    """
    recent_transactions = db_utils.execute_query(trans_query)
    
    context = {
        'total_properties': stats['total_properties'],
        'total_users': stats['total_users'],
        'total_agents': stats['total_agents'],
        'total_clients': stats['total_clients'],
        'total_transactions': stats['total_transactions'],
        'total_revenue': stats['total_revenue'],
        'recent_properties': recent_properties,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


# =====================================================
# PROFILE VIEWS (Raw SQL)
# =====================================================

@login_required_custom
def client_profile_create(request):
    """Create client profile - Raw SQL"""
    user_id = request.session.get('user_id')
    client = db_utils.get_client_by_user_id(user_id)
    
    if client:
        messages.info(request, 'Profile already exists.')
        return redirect('client_profile_update')
    
    if request.method == 'POST':
        form = ClientProfileForm(request.POST)
        if form.is_valid():
            try:
                profile_data = {
                    'preferred_contact_method': form.cleaned_data['preferred_contact_method'],
                    'budget_min': form.cleaned_data.get('budget_min'),
                    'budget_max': form.cleaned_data.get('budget_max'),
                    'preferred_location': form.cleaned_data.get('preferred_location'),
                    'looking_for': form.cleaned_data['looking_for']
                }
                db_utils.create_client_profile(user_id, profile_data)
                messages.success(request, 'Profile created successfully!')
                return redirect('client_dashboard')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = ClientProfileForm()
    
    return render(request, 'profile/client_profile_form.html', {'form': form, 'action': 'Create'})


@login_required_custom
def client_profile_update(request):
    """Update client profile - Raw SQL"""
    user_id = request.session.get('user_id')
    client = db_utils.get_client_by_user_id(user_id)
    
    if not client:
        return redirect('client_profile_create')
    
    if request.method == 'POST':
        form = ClientProfileForm(request.POST)
        if form.is_valid():
            try:
                profile_data = {
                    'preferred_contact_method': form.cleaned_data['preferred_contact_method'],
                    'budget_min': form.cleaned_data.get('budget_min'),
                    'budget_max': form.cleaned_data.get('budget_max'),
                    'preferred_location': form.cleaned_data.get('preferred_location'),
                    'looking_for': form.cleaned_data['looking_for']
                }
                db_utils.update_client_profile(client['client_id'], profile_data)
                messages.success(request, 'Profile updated!')
                return redirect('client_dashboard')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = ClientProfileForm(initial=client)
    
    return render(request, 'profile/client_profile_form.html', {'form': form, 'action': 'Update'})


@login_required_custom
def agent_profile_create(request):
    """Create agent profile - Raw SQL"""
    user_id = request.session.get('user_id')
    agent = db_utils.get_agent_by_user_id(user_id)
    
    if agent:
        messages.info(request, 'Profile already exists.')
        return redirect('agent_profile_update')
    
    if request.method == 'POST':
        form = AgentProfileForm(request.POST)
        if form.is_valid():
            try:
                profile_data = {
                    'license_number': form.cleaned_data['license_number'],
                    'agency_name': form.cleaned_data.get('agency_name'),
                    'commission_rate': form.cleaned_data.get('commission_rate', 3.00),
                    'specialization': form.cleaned_data.get('specialization'),
                    'years_experience': form.cleaned_data.get('years_experience', 0)
                }
                db_utils.create_agent_profile(user_id, profile_data)
                messages.success(request, 'Profile created!')
                return redirect('agent_dashboard')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = AgentProfileForm()
    
    return render(request, 'profile/agent_profile_form.html', {'form': form, 'action': 'Create'})


@login_required_custom
def agent_profile_update(request):
    """Update agent profile - Raw SQL"""
    user_id = request.session.get('user_id')
    agent = db_utils.get_agent_by_user_id(user_id)
    
    if not agent:
        return redirect('agent_profile_create')
    
    if request.method == 'POST':
        form = AgentProfileForm(request.POST)
        if form.is_valid():
            try:
                profile_data = {
                    'license_number': form.cleaned_data['license_number'],
                    'agency_name': form.cleaned_data.get('agency_name'),
                    'commission_rate': form.cleaned_data.get('commission_rate', 3.00),
                    'specialization': form.cleaned_data.get('specialization'),
                    'years_experience': form.cleaned_data.get('years_experience', 0)
                }
                db_utils.update_agent_profile(agent['agent_id'], profile_data)
                messages.success(request, 'Profile updated!')
                return redirect('agent_dashboard')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = AgentProfileForm(initial=agent)
    
    return render(request, 'profile/agent_profile_form.html', {'form': form, 'action': 'Update'})


# =====================================================
# PROPERTY VIEWS (100% Raw SQL)
# =====================================================

def property_list_view(request):
    """List properties - Raw SQL only"""
    form = PropertySearchForm(request.GET)
    filters = {}
    
    if form.is_valid():
        if form.cleaned_data.get('search_query'):
            filters['search_query'] = form.cleaned_data['search_query']
        if form.cleaned_data.get('listing_type'):
            filters['listing_type'] = form.cleaned_data['listing_type']
        if form.cleaned_data.get('property_type'):
            filters['property_type_id'] = int(form.cleaned_data['property_type'])
        if form.cleaned_data.get('min_price'):
            filters['min_price'] = form.cleaned_data['min_price']
        if form.cleaned_data.get('max_price'):
            filters['max_price'] = form.cleaned_data['max_price']
        if form.cleaned_data.get('min_bedrooms'):
            filters['min_bedrooms'] = form.cleaned_data['min_bedrooms']
        if form.cleaned_data.get('city'):
            filters['city'] = form.cleaned_data['city']
        if form.cleaned_data.get('status'):
            filters['status'] = form.cleaned_data['status']
        else:
            filters['status'] = 'available'
    else:
        filters['status'] = 'available'
    
    properties = db_utils.get_all_properties(filters)
    
    # Get images for each
    for prop in properties:
        images = db_utils.get_property_images(prop['property_id'])
        prop['images'] = images
    
    context = {
        'properties': properties,
        'form': form,
    }
    return render(request, 'properties/property_list.html', context)


def property_detail_view(request, pk):
    """Property detail - Raw SQL only"""
    property_obj = db_utils.get_property_by_id(pk)
    
    if not property_obj:
        messages.error(request, 'Property not found.')
        return redirect('property_list')
    
    # Get images
    images = db_utils.get_property_images(pk)
    
    # Get reviews
    reviews = db_utils.get_reviews_by_property(pk)
    
    # Calculate avg rating
    avg_rating = None
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
    
    # Check if can schedule
    can_schedule = False
    if request.user.is_authenticated and request.session.get('user_type') == 'client':
        client = db_utils.get_client_by_user_id(request.session.get('user_id'))
        can_schedule = client is not None
    
    context = {
        'property': property_obj,
        'images': images,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'can_schedule': can_schedule,
    }
    return render(request, 'properties/property_detail.html', context)


@login_required_custom
def property_create_view(request):
    """Create property - Raw SQL only"""
    if request.session.get('user_type') != 'agent':
        return HttpResponseForbidden("Only agents can create properties")
    
    user_id = request.session.get('user_id')
    agent = db_utils.get_agent_by_user_id(user_id)
    
    if not agent:
        messages.error(request, 'Complete your agent profile first.')
        return redirect('agent_profile_create')
    
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        
        if form.is_valid():
            try:
                location_data = {
                    'street_address': form.cleaned_data['street_address'],
                    'city': form.cleaned_data['city'],
                    'state': form.cleaned_data['state'],
                    'zip_code': form.cleaned_data['zip_code'],
                    'country': 'USA'
                }
                
                property_data = {
                    'property_type_id': int(form.cleaned_data['property_type']),
                    'title': form.cleaned_data['title'],
                    'description': form.cleaned_data.get('description', ''),
                    'price': form.cleaned_data['price'],
                    'listing_type': form.cleaned_data['listing_type'],
                    'bedrooms': form.cleaned_data['bedrooms'],
                    'bathrooms': form.cleaned_data['bathrooms'],
                    'square_feet': form.cleaned_data.get('square_feet'),
                    'lot_size': form.cleaned_data.get('lot_size'),
                    'year_built': form.cleaned_data.get('year_built'),
                    'status': form.cleaned_data.get('status', 'available'),
                    'listed_date': form.cleaned_data['listed_date'],
                    'parking_spaces': form.cleaned_data.get('parking_spaces', 0),
                    'has_garage': form.cleaned_data.get('has_garage', False),
                    'has_pool': form.cleaned_data.get('has_pool', False),
                    'has_garden': form.cleaned_data.get('has_garden', False)
                }
                
                property_id = db_utils.create_property(property_data, location_data, agent['agent_id'])
                
                messages.success(request, 'Property created successfully!')
                return redirect('property_detail', pk=property_id)
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = PropertyForm(initial={'listed_date': date.today()})
    
    return render(request, 'properties/property_form.html', {'form': form, 'action': 'Create'})


@login_required_custom
def property_update_view(request, pk):
    """Update property - Raw SQL only"""
    property_obj = db_utils.get_property_by_id(pk)
    
    if not property_obj:
        messages.error(request, 'Property not found.')
        return redirect('agent_dashboard')
    
    if request.session.get('user_type') != 'agent':
        return HttpResponseForbidden("Only agents can update properties")
    
    user_id = request.session.get('user_id')
    agent = db_utils.get_agent_by_user_id(user_id)
    
    if not agent or property_obj['agent_id'] != agent['agent_id']:
        return HttpResponseForbidden("You can only update your own properties")
    
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        
        if form.is_valid():
            try:
                location_data = {
                    'street_address': form.cleaned_data['street_address'],
                    'city': form.cleaned_data['city'],
                    'state': form.cleaned_data['state'],
                    'zip_code': form.cleaned_data['zip_code']
                }
                
                property_data = {
                    'property_type_id': int(form.cleaned_data['property_type']),
                    'title': form.cleaned_data['title'],
                    'description': form.cleaned_data.get('description', ''),
                    'price': form.cleaned_data['price'],
                    'listing_type': form.cleaned_data['listing_type'],
                    'bedrooms': form.cleaned_data['bedrooms'],
                    'bathrooms': form.cleaned_data['bathrooms'],
                    'square_feet': form.cleaned_data.get('square_feet'),
                    'lot_size': form.cleaned_data.get('lot_size'),
                    'year_built': form.cleaned_data.get('year_built'),
                    'status': form.cleaned_data['status'],
                    'parking_spaces': form.cleaned_data.get('parking_spaces', 0),
                    'has_garage': form.cleaned_data.get('has_garage', False),
                    'has_pool': form.cleaned_data.get('has_pool', False),
                    'has_garden': form.cleaned_data.get('has_garden', False)
                }
                
                db_utils.update_property(pk, property_data, location_data)
                
                messages.success(request, 'Property updated!')
                return redirect('property_detail', pk=pk)
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        initial = {
            'property_type': str(property_obj['property_type_id']),
            'title': property_obj['title'],
            'description': property_obj['description'],
            'price': property_obj['price'],
            'listing_type': property_obj['listing_type'],
            'bedrooms': property_obj['bedrooms'],
            'bathrooms': property_obj['bathrooms'],
            'square_feet': property_obj['square_feet'],
            'lot_size': property_obj['lot_size'],
            'year_built': property_obj['year_built'],
            'status': property_obj['status'],
            'listed_date': property_obj['listed_date'],
            'parking_spaces': property_obj['parking_spaces'],
            'has_garage': property_obj['has_garage'],
            'has_pool': property_obj['has_pool'],
            'has_garden': property_obj['has_garden'],
            'street_address': property_obj['street_address'],
            'city': property_obj['city'],
            'state': property_obj['state'],
            'zip_code': property_obj['zip_code']
        }
        form = PropertyForm(initial=initial)
    
    return render(request, 'properties/property_form.html', {'form': form, 'action': 'Update', 'property': property_obj})


@login_required_custom
def property_delete_view(request, pk):
    """Delete property - Raw SQL only"""
    property_obj = db_utils.get_property_by_id(pk)
    
    if not property_obj:
        messages.error(request, 'Property not found.')
        return redirect('agent_dashboard')
    
    if request.session.get('user_type') != 'agent':
        return HttpResponseForbidden("Only agents can delete")
    
    user_id = request.session.get('user_id')
    agent = db_utils.get_agent_by_user_id(user_id)
    
    if not agent or property_obj['agent_id'] != agent['agent_id']:
        return HttpResponseForbidden("Can only delete your own properties")
    
    if request.method == 'POST':
        try:
            title = property_obj['title']
            db_utils.delete_property(pk)
            messages.success(request, f'Property "{title}" deleted!')
            return redirect('agent_dashboard')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'properties/property_confirm_delete.html', {'property': property_obj})


# =====================================================
# APPOINTMENT VIEWS (100% Raw SQL)
# =====================================================

@login_required_custom
def appointment_create_view(request, property_pk):
    """Create appointment - Raw SQL only"""
    if request.session.get('user_type') != 'client':
        return HttpResponseForbidden("Only clients can schedule")
    
    property_obj = db_utils.get_property_by_id(property_pk)
    if not property_obj:
        messages.error(request, 'Property not found.')
        return redirect('property_list')
    
    user_id = request.session.get('user_id')
    client = db_utils.get_client_by_user_id(user_id)
    
    if not client:
        messages.error(request, 'Complete your profile first.')
        return redirect('client_profile_create')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            try:
                db_utils.create_appointment(
                    property_pk,
                    client['client_id'],
                    property_obj['agent_id'],
                    form.cleaned_data['appointment_date'],
                    form.cleaned_data.get('duration_minutes', 60),
                    form.cleaned_data.get('notes', '')
                )
                messages.success(request, 'Appointment scheduled!')
                return redirect('appointment_list')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = AppointmentForm()
    
    return render(request, 'appointments/appointment_form.html', {'form': form, 'property': property_obj, 'action': 'Schedule'})


@login_required_custom
def appointment_list_view(request):
    """List appointments - Raw SQL only"""
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type == 'client':
        client = db_utils.get_client_by_user_id(user_id)
        appointments = db_utils.get_appointments_by_client(client['client_id']) if client else []
    elif user_type == 'agent':
        agent = db_utils.get_agent_by_user_id(user_id)
        appointments = db_utils.get_appointments_by_agent(agent['agent_id']) if agent else []
    else:
        # Admin - get all appointments
        query = """
            SELECT a.*, p.title as property_title, p.property_id,
                l.city, l.state,
                c_user.first_name as client_first_name, c_user.last_name as client_last_name,
                a_user.first_name as agent_first_name, a_user.last_name as agent_last_name
            FROM Appointments a
            JOIN Properties p ON a.property_id = p.property_id
            JOIN Locations l ON p.location_id = l.location_id
            JOIN Clients c ON a.client_id = c.client_id
            JOIN Users c_user ON c.user_id = c_user.user_id
            JOIN Agents ag ON a.agent_id = ag.agent_id
            JOIN Users a_user ON ag.user_id = a_user.user_id
            ORDER BY a.appointment_date DESC
        """
        appointments = db_utils.execute_query(query)
    
    return render(request, 'appointments/appointment_list.html', {'appointments': appointments})


@login_required_custom
def appointment_update_view(request, pk):
    """Update appointment - Raw SQL only"""
    appointment = db_utils.get_appointment_by_id(pk)
    
    if not appointment:
        messages.error(request, 'Appointment not found.')
        return redirect('appointment_list')
    
    # Check permissions
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type == 'client':
        client = db_utils.get_client_by_user_id(user_id)
        if not client or appointment['client_id'] != client['client_id']:
            return HttpResponseForbidden("Access denied")
    elif user_type == 'agent':
        agent = db_utils.get_agent_by_user_id(user_id)
        if not agent or appointment['agent_id'] != agent['agent_id']:
            return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = AppointmentUpdateForm(request.POST)
        if form.is_valid():
            try:
                db_utils.update_appointment(
                    pk,
                    form.cleaned_data['status'],
                    form.cleaned_data.get('notes', '')
                )
                messages.success(request, 'Appointment updated!')
                return redirect('appointment_list')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = AppointmentUpdateForm(initial=appointment)
    
    # Get property for display
    property_obj = db_utils.get_property_by_id(appointment['property_id'])
    appointment['property'] = property_obj
    
    return render(request, 'appointments/appointment_update.html', {'form': form, 'appointment': appointment})


@login_required_custom
def appointment_delete_view(request, pk):
    """Delete appointment - Raw SQL only"""
    appointment = db_utils.get_appointment_by_id(pk)
    
    if not appointment:
        messages.error(request, 'Appointment not found.')
        return redirect('appointment_list')
    
    # Check permissions
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type == 'client':
        client = db_utils.get_client_by_user_id(user_id)
        if not client or appointment['client_id'] != client['client_id']:
            return HttpResponseForbidden("Access denied")
    elif user_type == 'agent':
        agent = db_utils.get_agent_by_user_id(user_id)
        if not agent or appointment['agent_id'] != agent['agent_id']:
            return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        try:
            db_utils.delete_appointment(pk)
            messages.success(request, 'Appointment cancelled!')
            return redirect('appointment_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    property_obj = db_utils.get_property_by_id(appointment['property_id'])
    appointment['property'] = property_obj
    
    return render(request, 'appointments/appointment_confirm_delete.html', {'appointment': appointment})


# =====================================================
# TRANSACTION VIEWS (100% Raw SQL)
# =====================================================

@login_required_custom
def transaction_create_view(request, property_pk):
    """Create transaction - Raw SQL only"""
    if request.session.get('user_type') != 'agent':
        return HttpResponseForbidden("Only agents can create transactions")
    
    property_obj = db_utils.get_property_by_id(property_pk)
    if not property_obj:
        messages.error(request, 'Property not found.')
        return redirect('agent_dashboard')
    
    user_id = request.session.get('user_id')
    agent = db_utils.get_agent_by_user_id(user_id)
    
    if not agent or property_obj['agent_id'] != agent['agent_id']:
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        client_id = request.POST.get('client_id')
        
        if form.is_valid() and client_id:
            try:
                transaction_data = {
                    'transaction_type': form.cleaned_data['transaction_type'],
                    'transaction_date': form.cleaned_data['transaction_date'],
                    'final_price': form.cleaned_data['final_price'],
                    'payment_status': form.cleaned_data.get('payment_status', 'completed'),
                    'lease_start_date': form.cleaned_data.get('lease_start_date'),
                    'lease_end_date': form.cleaned_data.get('lease_end_date'),
                    'notes': form.cleaned_data.get('notes', '')
                }
                
                db_utils.create_transaction(property_pk, int(client_id), agent['agent_id'], transaction_data)
                
                messages.success(request, 'Transaction created!')
                return redirect('transaction_list')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = TransactionForm(initial={
            'transaction_date': date.today(),
            'final_price': property_obj['price']
        })
    
    # Get potential clients
    potential_clients = db_utils.get_clients_for_property(property_pk)
    
    return render(request, 'transactions/transaction_form.html', {
        'form': form,
        'property': property_obj,
        'potential_clients': potential_clients,
        'action': 'Create'
    })


@login_required_custom
def transaction_list_view(request):
    """List transactions - Raw SQL only"""
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type == 'agent':
        agent = db_utils.get_agent_by_user_id(user_id)
        transactions = db_utils.get_transactions_by_agent(agent['agent_id']) if agent else []
    elif user_type == 'client':
        client = db_utils.get_client_by_user_id(user_id)
        transactions = db_utils.get_transactions_by_client(client['client_id']) if client else []
    else:
        query = """
            SELECT t.*, p.title as property_title
            FROM Transactions t
            JOIN Properties p ON t.property_id = p.property_id
            ORDER BY t.transaction_date DESC
        """
        transactions = db_utils.execute_query(query)
    
    return render(request, 'transactions/transaction_list.html', {'transactions': transactions})


@login_required_custom
def transaction_detail_view(request, pk):
    """Transaction detail - Raw SQL only"""
    transaction = db_utils.get_transaction_by_id(pk)
    
    if not transaction:
        messages.error(request, 'Transaction not found.')
        return redirect('transaction_list')
    
    # Check permissions
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type == 'client':
        client = db_utils.get_client_by_user_id(user_id)
        if not client or transaction['client_id'] != client['client_id']:
            return HttpResponseForbidden("Access denied")
    elif user_type == 'agent':
        agent = db_utils.get_agent_by_user_id(user_id)
        if not agent or transaction['agent_id'] != agent['agent_id']:
            return HttpResponseForbidden("Access denied")
    
    return render(request, 'transactions/transaction_detail.html', {'transaction': transaction})


# =====================================================
# REVIEW VIEWS (100% Raw SQL)
# =====================================================

@login_required_custom
def review_create_view(request, property_pk):
    """Create review - Raw SQL only"""
    if request.session.get('user_type') != 'client':
        return HttpResponseForbidden("Only clients can write reviews")
    
    property_obj = db_utils.get_property_by_id(property_pk)
    if not property_obj:
        messages.error(request, 'Property not found.')
        return redirect('property_list')
    
    user_id = request.session.get('user_id')
    client = db_utils.get_client_by_user_id(user_id)
    
    if not client:
        return redirect('client_profile_create')
    
    # Check if already reviewed
    if db_utils.check_review_exists(client['client_id'], property_pk):
        messages.warning(request, 'You already reviewed this property.')
        return redirect('property_detail', pk=property_pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                db_utils.create_review(
                    client['client_id'],
                    property_pk,
                    property_obj['agent_id'],
                    int(form.cleaned_data['rating']),
                    form.cleaned_data.get('review_text', '')
                )
                messages.success(request, 'Review submitted!')
                return redirect('property_detail', pk=property_pk)
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/review_form.html', {'form': form, 'property': property_obj})


@login_required_custom
def review_delete_view(request, pk):
    """Delete review - Raw SQL only"""
    review = db_utils.get_review_by_id(pk)
    
    if not review:
        messages.error(request, 'Review not found.')
        return redirect('client_dashboard')
    
    # Check permissions
    user_id = request.session.get('user_id')
    client = db_utils.get_client_by_user_id(user_id)
    
    if not client or (review['client_id'] != client['client_id'] and request.session.get('user_type') != 'admin'):
        return HttpResponseForbidden("Can only delete your own reviews")
    
    if request.method == 'POST':
        try:
            property_pk = review.get('property_id')
            db_utils.delete_review(pk)
            messages.success(request, 'Review deleted!')
            if property_pk:
                return redirect('property_detail', pk=property_pk)
            return redirect('client_dashboard')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'reviews/review_confirm_delete.html', {'review': review})


# =====================================================
# ANALYTICS VIEW (100% Raw SQL)
# =====================================================

@login_required_custom
def analytics_view(request):
    """Analytics dashboard - Raw SQL only"""
    if request.session.get('user_type') not in ['admin', 'agent']:
        return HttpResponseForbidden("Access denied")
    
    # Get analytics data using raw SQL
    analytics_data = db_utils.get_analytics_data()
    
    return render(request, 'analytics/analytics.html', analytics_data)