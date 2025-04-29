import os
import csv
import hashlib
import random
import string
from datetime import datetime
from .email_sender import send_verification_email

# Ruta a la base de datos de usuarios
USERS_DB_PATH = "data/users.csv"

def create_users_db_if_not_exists():
    """Crear base de datos de usuarios si no existe"""
    if not os.path.exists(USERS_DB_PATH):
        os.makedirs(os.path.dirname(USERS_DB_PATH), exist_ok=True)
        with open(USERS_DB_PATH, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'password_hash', 'email', 'verified', 'verification_code', 'created_at'])

def hash_password(password):
    """Encriptar una contraseña para guardarla"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(username, password):
    """Verificar si la combinación de usuario/contraseña es válida"""
    create_users_db_if_not_exists()
    
    with open(USERS_DB_PATH, 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username and row['password_hash'] == hash_password(password):
                return True
    return False

def username_exists(username):
    """Verificar si un nombre de usuario ya existe"""
    create_users_db_if_not_exists()
    
    if not os.path.exists(USERS_DB_PATH):
        return False
    
    with open(USERS_DB_PATH, 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                return True
    return False

def generate_verification_code():
    """Generar un código de verificación aleatorio"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def register_user(username, password, email):
    """Registrar un nuevo usuario"""
    create_users_db_if_not_exists()
    
    if username_exists(username):
        return False
    
    # Leer usuarios existentes
    users = []
    if os.path.exists(USERS_DB_PATH):
        with open(USERS_DB_PATH, 'r', newline='') as file:
            reader = csv.DictReader(file)
            users = list(reader)
    
    # Agregar nuevo usuario
    users.append({
        'username': username,
        'password_hash': hash_password(password),
        'email': email,
        'verified': 'True',  # Auto-verify user (no email verification)
        'verification_code': '',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Guardar todos los usuarios
    with open(USERS_DB_PATH, 'w', newline='') as file:
        fieldnames = ['username', 'password_hash', 'email', 'verified', 'verification_code', 'created_at']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)
    
    return True

def verify_email(username, verification_code):
    """Verificar el correo electrónico de un usuario con el código de verificación"""
    create_users_db_if_not_exists()
    
    users = []
    found = False
    
    with open(USERS_DB_PATH, 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username and row['verification_code'] == verification_code:
                row['verified'] = 'True'
                found = True
            users.append(row)
    
    if found:
        with open(USERS_DB_PATH, 'w', newline='') as file:
            fieldnames = ['username', 'password_hash', 'email', 'verified', 'verification_code', 'created_at']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)
        return True
    
    return False

def get_user_email(username):
    """Obtener el correo electrónico del usuario"""
    create_users_db_if_not_exists()
    
    with open(USERS_DB_PATH, 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                return row['email']
    return None

def change_password(username, new_password):
    """Cambiar la contraseña del usuario"""
    create_users_db_if_not_exists()
    
    users = []
    found = False
    
    with open(USERS_DB_PATH, 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                row['password_hash'] = hash_password(new_password)
                found = True
            users.append(row)
    
    if found:
        with open(USERS_DB_PATH, 'w', newline='') as file:
            fieldnames = ['username', 'password_hash', 'email', 'verified', 'verification_code', 'created_at']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)
        return True
    
    return False
