import os
import pandas as pd
import json
from datetime import datetime
import uuid

# Función para obtener la ruta del archivo de cuentas del usuario
def get_user_accounts_file(username):
    """Obtener la ruta al archivo de cuentas del usuario"""
    os.makedirs("data", exist_ok=True)
    os.makedirs(f"data/users", exist_ok=True)
    os.makedirs(f"data/users/{username}", exist_ok=True)
    return f"data/users/{username}/accounts.csv"

# Crear archivo de cuentas si no existe
def create_accounts_file_if_not_exists(username):
    """Crear archivo de cuentas si no existe"""
    file_path = get_user_accounts_file(username)
    if not os.path.exists(file_path):
        # Crear un DataFrame vacío con las columnas necesarias
        df = pd.DataFrame(columns=[
            'id', 'name', 'type', 'balance', 'currency', 'created_at', 'last_updated'
        ])
        df.to_csv(file_path, index=False)
        
        # Crear cuentas por defecto (Efectivo y Cuenta Bancaria)
        add_account(username, {
            'name': 'Efectivo',
            'type': 'cash',
            'balance': 0.0,
            'currency': 'ARS'
        })
        
        add_account(username, {
            'name': 'Cuenta Bancaria Principal',
            'type': 'bank',
            'balance': 0.0,
            'currency': 'ARS'
        })

# Cargar las cuentas del usuario
def load_user_accounts(username):
    """Cargar las cuentas de un usuario"""
    create_accounts_file_if_not_exists(username)
    file_path = get_user_accounts_file(username)
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            return pd.DataFrame(columns=[
                'id', 'name', 'type', 'balance', 'currency', 'created_at', 'last_updated'
            ])
        return df
    except Exception as e:
        print(f"Error al cargar cuentas: {e}")
        return pd.DataFrame(columns=[
            'id', 'name', 'type', 'balance', 'currency', 'created_at', 'last_updated'
        ])

# Obtener el siguiente ID para una cuenta
def get_next_account_id(username):
    """Obtener el siguiente ID disponible para una cuenta"""
    df = load_user_accounts(username)
    if df.empty:
        return 1
    try:
        return int(df['id'].max()) + 1
    except:
        return 1

# Añadir o actualizar una cuenta
def add_account(username, account_data):
    """Añadir una nueva cuenta o actualizar una existente para el usuario"""
    df = load_user_accounts(username)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Verificar si es una edición (tiene ID) o una nueva cuenta
    is_edit = account_data.get('id') is not None
    
    if is_edit:
        # Obtener el ID existente
        account_id = int(account_data.get('id'))
        
        # Verificar si la cuenta existe
        if account_id in df['id'].values:
            # Actualizar cuenta existente
            idx = df[df['id'] == account_id].index[0]
            
            # Actualizar los campos
            df.at[idx, 'name'] = account_data.get('name', df.at[idx, 'name'])
            df.at[idx, 'type'] = account_data.get('type', df.at[idx, 'type'])
            df.at[idx, 'balance'] = float(account_data.get('balance', df.at[idx, 'balance']))
            df.at[idx, 'currency'] = account_data.get('currency', df.at[idx, 'currency'])
            df.at[idx, 'last_updated'] = now
            
            # Guardar el DataFrame actualizado
            file_path = get_user_accounts_file(username)
            df.to_csv(file_path, index=False)
            
            return df.iloc[idx].to_dict()
    
    # Si no es una edición válida o es una nueva cuenta
    new_account = {
        'id': account_data.get('id') if is_edit else get_next_account_id(username),
        'name': account_data.get('name', 'Nueva Cuenta'),
        'type': account_data.get('type', 'other'),
        'balance': float(account_data.get('balance', 0.0)),
        'currency': account_data.get('currency', 'ARS'),
        'created_at': now,
        'last_updated': now
    }
    
    # Añadir la nueva cuenta al DataFrame
    df = pd.concat([df, pd.DataFrame([new_account])], ignore_index=True)
    
    # Guardar el DataFrame actualizado
    file_path = get_user_accounts_file(username)
    df.to_csv(file_path, index=False)
    
    return new_account

# Eliminar una cuenta
def delete_account(username, account_id):
    """Eliminar una cuenta por ID"""
    df = load_user_accounts(username)
    if account_id not in df['id'].values:
        return False
    
    # Filtrar para eliminar la cuenta
    df = df[df['id'] != account_id]
    
    # Guardar el DataFrame actualizado
    file_path = get_user_accounts_file(username)
    df.to_csv(file_path, index=False)
    
    return True

# Obtener una cuenta por ID
def get_account_by_id(username, account_id):
    """Obtener una cuenta por ID"""
    df = load_user_accounts(username)
    account = df[df['id'] == account_id]
    if account.empty:
        return None
    return account.iloc[0].to_dict()

# Actualizar el saldo de una cuenta
def update_account_balance(username, account_id, amount, operation='add'):
    """
    Actualizar el saldo de una cuenta
    
    Args:
        username: Nombre de usuario
        account_id: ID de la cuenta
        amount: Cantidad a añadir o restar
        operation: 'add' para sumar, 'subtract' para restar
    """
    df = load_user_accounts(username)
    
    # Verificar si la cuenta existe
    if int(account_id) not in df['id'].values:
        return False
    
    # Buscar el índice de la cuenta
    idx = df[df['id'] == int(account_id)].index[0]
    
    # Actualizar el saldo según la operación
    if operation == 'add':
        df.at[idx, 'balance'] = df.at[idx, 'balance'] + float(amount)
    elif operation == 'subtract':
        df.at[idx, 'balance'] = df.at[idx, 'balance'] - float(amount)
    
    # Actualizar fecha de última modificación
    df.at[idx, 'last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Guardar el DataFrame actualizado
    file_path = get_user_accounts_file(username)
    df.to_csv(file_path, index=False)
    
    return True

# Obtener tipos de cuentas predefinidos
def get_account_types():
    """Obtener tipos de cuentas predefinidos"""
    return {
        'bank': 'Cuenta Bancaria',
        'cash': 'Efectivo',
        'credit_card': 'Tarjeta de Crédito',
        'investment': 'Inversión',
        'savings': 'Cuenta de Ahorro',
        'digital_wallet': 'Billetera Digital',
        'other': 'Otra'
    }