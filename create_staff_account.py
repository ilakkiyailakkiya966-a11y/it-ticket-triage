"""
Run this ONCE to create your first IT Staff login.
Usage: python create_staff_account.py
"""
from werkzeug.security import generate_password_hash
from database import init_db, create_user

init_db()

username = input("Choose a username for the IT Staff account: ").strip()
password = input("Choose a password: ").strip()

password_hash = generate_password_hash(password)
success = create_user(username, password_hash, role="it_staff")

if success:
    print(f"IT Staff account '{username}' created successfully!")
else:
    print(f"Username '{username}' is already taken. Try a different one.")
