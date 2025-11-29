import hashlib
import os
import binascii

def hash_password(password):
    """Hash password using PBKDF2-SHA256"""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

# Generate hashes for your test accounts
admin_hash = hash_password('admin123')
agent_hash = hash_password('agent123')
client_hash = hash_password('client123')

print("="*60)
print("PASSWORD HASHES GENERATED")
print("="*60)
print(f"\nAdmin (admin12):")
print(admin_hash)
print(f"\nAgent (agent123):")
print(agent_hash)
print(f"\nClient (client123):")
print(client_hash)
print("\n" + "="*60)
print("Copy these hashes to use in SQL UPDATE statements")
print("="*60)