"""
Real Estate DBMS - Database Utilities
"""

import pymysql
from pymysql.cursors import DictCursor
import os
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Create and return a database connection using PyMySQL"""
    try:
        connection = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'real_estate_db'),
            port=int(os.getenv('DB_PORT', 3306)),
            charset='utf8mb4',
            cursorclass=DictCursor,
            autocommit=False
        )
        return connection
    except pymysql.Error as e:
        print(f"Error connecting to database: {e}")
        raise


def execute_query(query, params=None):
    """Execute a SELECT query and return results"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
    except pymysql.Error as e:
        print(f"Query error: {e}")
        raise
    finally:
        connection.close()


def execute_update(query, params=None):
    """Execute INSERT, UPDATE, or DELETE query"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            affected_rows = cursor.execute(query, params or ())
            connection.commit()
            return affected_rows
    except pymysql.Error as e:
        connection.rollback()
        print(f"Update error: {e}")
        raise
    finally:
        connection.close()


def execute_insert(query, params=None):
    """Execute INSERT query and return the last inserted ID"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            last_id = cursor.lastrowid
            connection.commit()
            return last_id
    except pymysql.Error as e:
        connection.rollback()
        print(f"Insert error: {e}")
        raise
    finally:
        connection.close()


# =====================================================
# PROPERTY QUERIES
# =====================================================

def get_all_properties(filters=None):
    """Get all properties with optional filters"""
    query = """
        SELECT 
            p.property_id, p.title, p.description, p.price, p.listing_type,
            p.bedrooms, p.bathrooms, p.square_feet, p.status, p.listed_date,
            p.parking_spaces, p.has_garage, p.has_pool, p.has_garden,
            p.year_built, p.lot_size, p.sold_date,
            l.location_id, l.street_address, l.city, l.state, l.zip_code,
            pt.property_type_id, pt.type_name,
            a.agent_id, a.agency_name, a.rating as agent_rating,
            u.first_name as agent_first_name, u.last_name as agent_last_name,
            u.email as agent_email, u.phone as agent_phone
        FROM Properties p
        JOIN Locations l ON p.location_id = l.location_id
        JOIN PropertyTypes pt ON p.property_type_id = pt.property_type_id
        JOIN Agents a ON p.agent_id = a.agent_id
        JOIN Users u ON a.user_id = u.user_id
        WHERE 1=1
    """
    
    params = []
    
    if filters:
        if filters.get('status'):
            query += " AND p.status = %s"
            params.append(filters['status'])
        
        if filters.get('listing_type'):
            query += " AND p.listing_type = %s"
            params.append(filters['listing_type'])
        
        if filters.get('min_price'):
            query += " AND p.price >= %s"
            params.append(filters['min_price'])
        
        if filters.get('max_price'):
            query += " AND p.price <= %s"
            params.append(filters['max_price'])
        
        if filters.get('city'):
            query += " AND l.city LIKE %s"
            params.append(f"%{filters['city']}%")
        
        if filters.get('min_bedrooms'):
            query += " AND p.bedrooms >= %s"
            params.append(filters['min_bedrooms'])
        
        if filters.get('property_type_id'):
            query += " AND p.property_type_id = %s"
            params.append(filters['property_type_id'])
        
        if filters.get('search_query'):
            query += " AND (p.title LIKE %s OR p.description LIKE %s OR l.city LIKE %s)"
            search_term = f"%{filters['search_query']}%"
            params.extend([search_term, search_term, search_term])
    
    query += " ORDER BY p.listed_date DESC"
    
    return execute_query(query, tuple(params) if params else None)


def get_property_by_id(property_id):
    """Get a single property by ID"""
    query = """
        SELECT 
            p.*,
            l.location_id, l.street_address, l.city, l.state, l.zip_code,
            pt.property_type_id, pt.type_name, pt.description as type_description,
            a.agent_id, a.license_number, a.agency_name, a.rating as agent_rating, a.years_experience, a.total_sales,
            u.user_id, u.first_name as agent_first_name, u.last_name as agent_last_name,
            u.email as agent_email, u.phone as agent_phone
        FROM Properties p
        JOIN Locations l ON p.location_id = l.location_id
        JOIN PropertyTypes pt ON p.property_type_id = pt.property_type_id
        JOIN Agents a ON p.agent_id = a.agent_id
        JOIN Users u ON a.user_id = u.user_id
        WHERE p.property_id = %s
    """
    
    results = execute_query(query, (property_id,))
    return results[0] if results else None


def create_property(property_data, location_data, agent_id):
    """Create a new property with location"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Insert location first
            location_query = """
                INSERT INTO Locations (street_address, city, state, zip_code, country)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(location_query, (
                location_data['street_address'],
                location_data['city'],
                location_data['state'],
                location_data['zip_code'],
                location_data.get('country', 'USA')
            ))
            location_id = cursor.lastrowid
            
            # Insert property
            property_query = """
                INSERT INTO Properties (
                    location_id, property_type_id, agent_id, title, description,
                    price, listing_type, bedrooms, bathrooms, square_feet, lot_size,
                    year_built, status, listed_date, parking_spaces, has_garage,
                    has_pool, has_garden
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(property_query, (
                location_id,
                property_data['property_type_id'],
                agent_id,
                property_data['title'],
                property_data.get('description', ''),
                property_data['price'],
                property_data['listing_type'],
                property_data['bedrooms'],
                property_data['bathrooms'],
                property_data.get('square_feet'),
                property_data.get('lot_size'),
                property_data.get('year_built'),
                property_data.get('status', 'available'),
                property_data['listed_date'],
                property_data.get('parking_spaces', 0),
                property_data.get('has_garage', False),
                property_data.get('has_pool', False),
                property_data.get('has_garden', False)
            ))
            property_id = cursor.lastrowid
            
            connection.commit()
            return property_id
    except pymysql.Error as e:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_property(property_id, property_data, location_data):
    """Update existing property"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Get location_id
            cursor.execute("SELECT location_id FROM Properties WHERE property_id = %s", (property_id,))
            result = cursor.fetchone()
            location_id = result['location_id']
            
            # Update location
            location_query = """
                UPDATE Locations 
                SET street_address = %s, city = %s, state = %s, zip_code = %s
                WHERE location_id = %s
            """
            cursor.execute(location_query, (
                location_data['street_address'],
                location_data['city'],
                location_data['state'],
                location_data['zip_code'],
                location_id
            ))
            
            # Update property
            property_query = """
                UPDATE Properties
                SET property_type_id = %s, title = %s, description = %s, price = %s,
                    listing_type = %s, bedrooms = %s, bathrooms = %s, square_feet = %s,
                    lot_size = %s, year_built = %s, status = %s, parking_spaces = %s,
                    has_garage = %s, has_pool = %s, has_garden = %s, updated_at = NOW()
                WHERE property_id = %s
            """
            cursor.execute(property_query, (
                property_data['property_type_id'],
                property_data['title'],
                property_data.get('description', ''),
                property_data['price'],
                property_data['listing_type'],
                property_data['bedrooms'],
                property_data['bathrooms'],
                property_data.get('square_feet'),
                property_data.get('lot_size'),
                property_data.get('year_built'),
                property_data['status'],
                property_data.get('parking_spaces', 0),
                property_data.get('has_garage', False),
                property_data.get('has_pool', False),
                property_data.get('has_garden', False),
                property_id
            ))
            
            connection.commit()
            return cursor.rowcount
    except pymysql.Error as e:
        connection.rollback()
        raise
    finally:
        connection.close()


def delete_property(property_id):
    """Delete a property"""
    query = "DELETE FROM Properties WHERE property_id = %s"
    return execute_update(query, (property_id,))


# =====================================================
# APPOINTMENT QUERIES
# =====================================================

def get_appointments_by_client(client_id):
    """Get all appointments for a client"""
    query = """
        SELECT 
            a.appointment_id, a.appointment_date, a.duration_minutes, a.status, a.notes,
            p.property_id, p.title as property_title,
            l.city, l.state,
            ag.agent_id, u.first_name as agent_first_name, u.last_name as agent_last_name
        FROM Appointments a
        JOIN Properties p ON a.property_id = p.property_id
        JOIN Locations l ON p.location_id = l.location_id
        JOIN Agents ag ON a.agent_id = ag.agent_id
        JOIN Users u ON ag.user_id = u.user_id
        WHERE a.client_id = %s
        ORDER BY a.appointment_date DESC
    """
    return execute_query(query, (client_id,))


def get_appointments_by_agent(agent_id):
    """Get all appointments for an agent"""
    query = """
        SELECT 
            a.appointment_id, a.appointment_date, a.duration_minutes, a.status, a.notes,
            p.property_id, p.title as property_title,
            l.city, l.state,
            c.client_id, u.first_name as client_first_name, u.last_name as client_last_name
        FROM Appointments a
        JOIN Properties p ON a.property_id = p.property_id
        JOIN Locations l ON p.location_id = l.location_id
        JOIN Clients c ON a.client_id = c.client_id
        JOIN Users u ON c.user_id = u.user_id
        WHERE a.agent_id = %s
        ORDER BY a.appointment_date DESC
    """
    return execute_query(query, (agent_id,))


def create_appointment(property_id, client_id, agent_id, appointment_date, duration_minutes, notes):
    """Create a new appointment"""
    query = """
        INSERT INTO Appointments (property_id, client_id, agent_id, appointment_date, duration_minutes, status, notes)
        VALUES (%s, %s, %s, %s, %s, 'scheduled', %s)
    """
    return execute_insert(query, (property_id, client_id, agent_id, appointment_date, duration_minutes, notes))


def update_appointment(appointment_id, status, notes):
    """Update appointment status and notes"""
    query = """
        UPDATE Appointments
        SET status = %s, notes = %s, updated_at = NOW()
        WHERE appointment_id = %s
    """
    return execute_update(query, (status, notes, appointment_id))


def delete_appointment(appointment_id):
    """Delete an appointment"""
    query = "DELETE FROM Appointments WHERE appointment_id = %s"
    return execute_update(query, (appointment_id,))


def get_appointment_by_id(appointment_id):
    """Get appointment by ID"""
    query = "SELECT * FROM Appointments WHERE appointment_id = %s"
    results = execute_query(query, (appointment_id,))
    return results[0] if results else None


# =====================================================
# TRANSACTION QUERIES
# =====================================================

def get_transactions_by_agent(agent_id):
    """Get all transactions for an agent"""
    query = """
        SELECT 
            t.transaction_id, t.transaction_type, t.transaction_date, t.final_price,
            t.commission_amount, t.payment_status, t.notes,
            p.property_id, p.title as property_title,
            c.client_id, u.first_name as client_first_name, u.last_name as client_last_name
        FROM Transactions t
        JOIN Properties p ON t.property_id = p.property_id
        JOIN Clients c ON t.client_id = c.client_id
        JOIN Users u ON c.user_id = u.user_id
        WHERE t.agent_id = %s
        ORDER BY t.transaction_date DESC
    """
    return execute_query(query, (agent_id,))


def get_transactions_by_client(client_id):
    """Get all transactions for a client"""
    query = """
        SELECT 
            t.transaction_id, t.transaction_type, t.transaction_date, t.final_price,
            t.commission_amount, t.payment_status,
            p.property_id, p.title as property_title,
            a.agent_id, u.first_name as agent_first_name, u.last_name as agent_last_name
        FROM Transactions t
        JOIN Properties p ON t.property_id = p.property_id
        JOIN Agents a ON t.agent_id = a.agent_id
        JOIN Users u ON a.user_id = u.user_id
        WHERE t.client_id = %s
        ORDER BY t.transaction_date DESC
    """
    return execute_query(query, (client_id,))


def get_transaction_by_id(transaction_id):
    """Get transaction details"""
    query = """
        SELECT 
            t.*,
            p.property_id, p.title as property_title,
            l.street_address, l.city, l.state, l.zip_code,
            c.client_id, c_user.first_name as client_first_name, c_user.last_name as client_last_name,
            c_user.email as client_email,
            a.agent_id, a.agency_name, a_user.first_name as agent_first_name, 
            a_user.last_name as agent_last_name, a_user.email as agent_email
        FROM Transactions t
        JOIN Properties p ON t.property_id = p.property_id
        JOIN Locations l ON p.location_id = l.location_id
        JOIN Clients c ON t.client_id = c.client_id
        JOIN Users c_user ON c.user_id = c_user.user_id
        JOIN Agents a ON t.agent_id = a.agent_id
        JOIN Users a_user ON a.user_id = a_user.user_id
        WHERE t.transaction_id = %s
    """
    results = execute_query(query, (transaction_id,))
    return results[0] if results else None


def create_transaction(property_id, client_id, agent_id, transaction_data):
    """Create a new transaction"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Get agent commission rate
            cursor.execute("SELECT commission_rate FROM Agents WHERE agent_id = %s", (agent_id,))
            agent_data = cursor.fetchone()
            commission_rate = agent_data['commission_rate']
            
            # Calculate commission
            commission_amount = transaction_data['final_price'] * (commission_rate / 100)
            
            # Insert transaction
            transaction_query = """
                INSERT INTO Transactions (
                    property_id, client_id, agent_id, transaction_type, transaction_date,
                    final_price, commission_amount, payment_status, lease_start_date,
                    lease_end_date, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(transaction_query, (
                property_id, client_id, agent_id,
                transaction_data['transaction_type'],
                transaction_data['transaction_date'],
                transaction_data['final_price'],
                commission_amount,
                transaction_data.get('payment_status', 'completed'),
                transaction_data.get('lease_start_date'),
                transaction_data.get('lease_end_date'),
                transaction_data.get('notes', '')
            ))
            transaction_id = cursor.lastrowid
            
            # Update property status
            new_status = 'sold' if transaction_data['transaction_type'] == 'sale' else 'rented'
            cursor.execute("""
                UPDATE Properties 
                SET status = %s, sold_date = %s
                WHERE property_id = %s
            """, (new_status, transaction_data['transaction_date'], property_id))
            
            # Update agent total_sales
            cursor.execute("""
                UPDATE Agents 
                SET total_sales = total_sales + 1
                WHERE agent_id = %s
            """, (agent_id,))
            
            connection.commit()
            return transaction_id
    except pymysql.Error as e:
        connection.rollback()
        raise
    finally:
        connection.close()


# =====================================================
# REVIEW QUERIES
# =====================================================

def get_reviews_by_property(property_id):
    """Get all reviews for a property"""
    query = """
        SELECT 
            r.review_id, r.rating, r.review_text, r.review_date, r.is_verified,
            c.client_id, u.first_name as client_first_name, u.last_name as client_last_name
        FROM Reviews r
        JOIN Clients c ON r.client_id = c.client_id
        JOIN Users u ON c.user_id = u.user_id
        WHERE r.property_id = %s
        ORDER BY r.review_date DESC
    """
    return execute_query(query, (property_id,))


def get_review_by_id(review_id):
    """Get review by ID"""
    query = """
        SELECT r.*, p.property_id, p.title as property_title
        FROM Reviews r
        LEFT JOIN Properties p ON r.property_id = p.property_id
        WHERE r.review_id = %s
    """
    results = execute_query(query, (review_id,))
    return results[0] if results else None


def check_review_exists(client_id, property_id):
    """Check if client already reviewed this property"""
    query = "SELECT COUNT(*) as count FROM Reviews WHERE client_id = %s AND property_id = %s"
    result = execute_query(query, (client_id, property_id))
    return result[0]['count'] > 0


def create_review(client_id, property_id, agent_id, rating, review_text):
    """Create a new review"""
    query = """
        INSERT INTO Reviews (client_id, property_id, agent_id, rating, review_text, is_verified)
        VALUES (%s, %s, %s, %s, %s, FALSE)
    """
    return execute_insert(query, (client_id, property_id, agent_id, rating, review_text))


def delete_review(review_id):
    """Delete a review"""
    query = "DELETE FROM Reviews WHERE review_id = %s"
    return execute_update(query, (review_id,))


# =====================================================
# USER/PROFILE QUERIES
# =====================================================

def get_user_by_id(user_id):
    """Get user by ID"""
    query = """
        SELECT user_id, email, username, first_name, last_name, phone,
               user_type, is_active, is_superuser, is_staff
        FROM Users
        WHERE user_id = %s
    """
    results = execute_query(query, (user_id,))
    return results[0] if results else None


def get_user_by_email(email):
    """Get user by email"""
    query = "SELECT * FROM Users WHERE email = %s"
    results = execute_query(query, (email,))
    return results[0] if results else None


def get_client_by_user_id(user_id):
    """Get client profile"""
    query = """
        SELECT c.*, u.first_name, u.last_name, u.email, u.phone
        FROM Clients c
        JOIN Users u ON c.user_id = u.user_id
        WHERE c.user_id = %s
    """
    results = execute_query(query, (user_id,))
    return results[0] if results else None


def get_agent_by_user_id(user_id):
    """Get agent profile"""
    query = """
        SELECT a.*, u.first_name, u.last_name, u.email, u.phone
        FROM Agents a
        JOIN Users u ON a.user_id = u.user_id
        WHERE a.user_id = %s
    """
    results = execute_query(query, (user_id,))
    return results[0] if results else None


def create_client_profile(user_id, profile_data):
    """Create client profile"""
    query = """
        INSERT INTO Clients (user_id, preferred_contact_method, budget_min, budget_max, preferred_location, looking_for)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return execute_insert(query, (
        user_id,
        profile_data['preferred_contact_method'],
        profile_data.get('budget_min'),
        profile_data.get('budget_max'),
        profile_data.get('preferred_location'),
        profile_data['looking_for']
    ))


def create_agent_profile(user_id, profile_data):
    """Create agent profile"""
    query = """
        INSERT INTO Agents (user_id, license_number, agency_name, commission_rate, specialization, years_experience)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return execute_insert(query, (
        user_id,
        profile_data['license_number'],
        profile_data.get('agency_name'),
        profile_data.get('commission_rate', 3.00),
        profile_data.get('specialization'),
        profile_data.get('years_experience', 0)
    ))


def update_client_profile(client_id, profile_data):
    """Update client profile"""
    query = """
        UPDATE Clients
        SET preferred_contact_method = %s, budget_min = %s, budget_max = %s,
            preferred_location = %s, looking_for = %s
        WHERE client_id = %s
    """
    return execute_update(query, (
        profile_data['preferred_contact_method'],
        profile_data.get('budget_min'),
        profile_data.get('budget_max'),
        profile_data.get('preferred_location'),
        profile_data['looking_for'],
        client_id
    ))


def update_agent_profile(agent_id, profile_data):
    """Update agent profile"""
    query = """
        UPDATE Agents
        SET license_number = %s, agency_name = %s, commission_rate = %s,
            specialization = %s, years_experience = %s
        WHERE agent_id = %s
    """
    return execute_update(query, (
        profile_data['license_number'],
        profile_data.get('agency_name'),
        profile_data.get('commission_rate', 3.00),
        profile_data.get('specialization'),
        profile_data.get('years_experience', 0),
        agent_id
    ))


# =====================================================
# PROPERTY IMAGES
# =====================================================

def get_property_images(property_id):
    """Get all images for a property"""
    query = """
        SELECT image_id, image_url, caption, is_primary, display_order
        FROM PropertyImages
        WHERE property_id = %s
        ORDER BY display_order
    """
    return execute_query(query, (property_id,))


# =====================================================
# PROPERTY TYPES
# =====================================================

def get_all_property_types():
    """Get all property types"""
    query = "SELECT property_type_id, type_name, description FROM PropertyTypes ORDER BY type_name"
    return execute_query(query)


# =====================================================
# ANALYTICS QUERIES
# =====================================================

def get_analytics_data():
    """Get comprehensive analytics data"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Total properties
            cursor.execute("SELECT COUNT(*) as total FROM Properties")
            total_properties = cursor.fetchone()['total']
            
            # Available properties
            cursor.execute("SELECT COUNT(*) as total FROM Properties WHERE status = 'available'")
            available_properties = cursor.fetchone()['total']
            
            # Sold properties
            cursor.execute("SELECT COUNT(*) as total FROM Properties WHERE status = 'sold'")
            sold_properties = cursor.fetchone()['total']
            
            # Average price
            cursor.execute("SELECT AVG(price) as avg_price FROM Properties WHERE status = 'available'")
            avg_price = cursor.fetchone()['avg_price'] or 0
            
            # Properties by type
            cursor.execute("""
                SELECT pt.type_name as property_type__type_name, COUNT(*) as count
                FROM Properties p
                JOIN PropertyTypes pt ON p.property_type_id = pt.property_type_id
                GROUP BY pt.type_name
                ORDER BY count DESC
            """)
            properties_by_type = cursor.fetchall()
            
            # Properties by city
            cursor.execute("""
                SELECT l.city as location__city, COUNT(*) as count
                FROM Properties p
                JOIN Locations l ON p.location_id = l.location_id
                GROUP BY l.city
                ORDER BY count DESC
                LIMIT 10
            """)
            properties_by_city = cursor.fetchall()
            
            return {
                'total_properties': total_properties,
                'available_properties': available_properties,
                'sold_properties': sold_properties,
                'avg_price': avg_price,
                'properties_by_type': properties_by_type,
                'properties_by_city': properties_by_city
            }
    finally:
        connection.close()


def get_agent_total_commission(agent_id):
    """Get total commission for an agent"""
    query = """
        SELECT COALESCE(SUM(commission_amount), 0) as total_commission
        FROM Transactions
        WHERE agent_id = %s AND payment_status = 'completed'
    """
    result = execute_query(query, (agent_id,))
    return result[0]['total_commission'] if result else 0


def get_properties_by_agent(agent_id):
    """Get all properties for an agent"""
    query = """
        SELECT p.*, l.city, l.state, pt.type_name
        FROM Properties p
        JOIN Locations l ON p.location_id = l.location_id
        JOIN PropertyTypes pt ON p.property_type_id = pt.property_type_id
        WHERE p.agent_id = %s
        ORDER BY p.created_at DESC
    """
    return execute_query(query, (agent_id,))


def get_clients_for_property(property_id):
    """Get clients who have appointments for a property"""
    query = """
        SELECT DISTINCT c.client_id, u.first_name, u.last_name, u.email
        FROM Clients c
        JOIN Users u ON c.user_id = u.user_id
        JOIN Appointments a ON c.client_id = a.client_id
        WHERE a.property_id = %s
    """
    return execute_query(query, (property_id,))