import os
import csv
import pandas as pd
from datetime import datetime
import sys

def get_user_transactions_file(username):
    """Get the path to a user's transactions file"""
    os.makedirs("data", exist_ok=True)
    os.makedirs(f"data/users", exist_ok=True)
    os.makedirs(f"data/users/{username}", exist_ok=True)
    return f"data/users/{username}/transactions.csv"

def create_transactions_file_if_not_exists(username):
    """Create transactions file if it doesn't exist"""
    file_path = get_user_transactions_file(username)
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'id', 'date', 'type', 'category', 'subcategory', 'description', 
                'amount', 'currency', 'exchange_rate', 'amount_pesos',
                'payment_method', 'fixed_expense', 'installments_total', 
                'installments_paid', 'created_at', 'account_id'
            ])

def load_user_data(username):
    """Load a user's transaction data"""
    create_transactions_file_if_not_exists(username)
    
    file_path = get_user_transactions_file(username)
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading user data: {e}")
        return pd.DataFrame(columns=[
            'id', 'date', 'type', 'category', 'subcategory', 'description', 
            'amount', 'currency', 'exchange_rate', 'amount_pesos',
            'payment_method', 'fixed_expense', 'installments_total', 
            'installments_paid', 'created_at', 'account_id'
        ])

def get_next_id(username):
    """Get the next available ID for a transaction"""
    df = load_user_data(username)
    if df.empty:
        return 1
    return df['id'].max() + 1

def save_transaction(username, transaction_data):
    """Save a new transaction for a user"""
    create_transactions_file_if_not_exists(username)
    
    df = load_user_data(username)
    
    # Add transaction ID if not present
    if 'id' not in transaction_data or pd.isna(transaction_data['id']):
        transaction_data['id'] = get_next_id(username)
    
    # Add created_at if not present
    if 'created_at' not in transaction_data:
        transaction_data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Determine if this is a new transaction or an update
    is_update = False
    old_transaction = None
    if len(df[df['id'] == transaction_data['id']]) > 0:
        # Estamos actualizando una transacción existente
        is_update = True
        old_transaction = df[df['id'] == transaction_data['id']].iloc[0].to_dict()
        df = df[df['id'] != transaction_data['id']]
    
    # Append new transaction
    df = pd.concat([df, pd.DataFrame([transaction_data])], ignore_index=True)
    
    # Save back to file
    file_path = get_user_transactions_file(username)
    df.to_csv(file_path, index=False)
    
    # Actualizar saldos de cuentas
    # Si tenemos un account_id, actualizamos su saldo
    try:
        # Importamos aquí para evitar importaciones circulares
        from utils.accounts import update_account_balance
        
        # Si es una actualización, primero revertimos la transacción anterior
        if is_update and old_transaction.get('account_id'):
            old_account_id = old_transaction.get('account_id')
            old_amount = float(old_transaction.get('amount', 0))
            old_type = old_transaction.get('type', '')
            
            # Revertir la operación anterior
            if old_type == 'Ingreso':
                update_account_balance(username, old_account_id, old_amount, 'subtract')
            elif old_type == 'Gasto':
                update_account_balance(username, old_account_id, old_amount, 'add')
        
        # Aplicar la nueva transacción
        if transaction_data.get('account_id'):
            account_id = transaction_data.get('account_id')
            amount = float(transaction_data.get('amount', 0))
            transaction_type = transaction_data.get('type', '')
            
            # Actualizar el saldo de la cuenta según el tipo de transacción
            if transaction_type == 'Ingreso':
                update_account_balance(username, account_id, amount, 'add')
            elif transaction_type == 'Gasto':
                update_account_balance(username, account_id, amount, 'subtract')
    except Exception as e:
        print(f"Error al actualizar saldo de cuenta: {e}")
    
    return True

def delete_transaction(username, transaction_id):
    """Delete a transaction by ID"""
    create_transactions_file_if_not_exists(username)
    
    df = load_user_data(username)
    
    # Obtener la transacción antes de eliminarla para revertir su efecto en la cuenta
    transaction = df[df['id'] == transaction_id]
    if not transaction.empty:
        try:
            # Importamos aquí para evitar importaciones circulares
            from utils.accounts import update_account_balance
            
            # Obtener datos de la transacción
            transaction_data = transaction.iloc[0].to_dict()
            if transaction_data.get('account_id'):
                account_id = transaction_data.get('account_id')
                amount = float(transaction_data.get('amount', 0))
                transaction_type = transaction_data.get('type', '')
                
                # Revertir el efecto en la cuenta
                if transaction_type == 'Ingreso':
                    update_account_balance(username, account_id, amount, 'subtract')
                elif transaction_type == 'Gasto':
                    update_account_balance(username, account_id, amount, 'add')
        except Exception as e:
            print(f"Error al revertir saldo de cuenta: {e}")
    
    # Filtrar para eliminar la transacción
    df = df[df['id'] != transaction_id]
    
    # Guardar en el archivo
    file_path = get_user_transactions_file(username)
    df.to_csv(file_path, index=False)
    return True

def get_transaction_by_id(username, transaction_id):
    """Get a transaction by ID"""
    df = load_user_data(username)
    transaction = df[df['id'] == transaction_id]
    if transaction.empty:
        return None
    return transaction.iloc[0].to_dict()

def filter_transactions(df, filters):
    """Filter transactions based on given criteria"""
    filtered_df = df.copy()
    
    # Filter by date range
    if 'start_date' in filters and filters['start_date']:
        filtered_df = filtered_df[filtered_df['date'] >= filters['start_date']]
    
    if 'end_date' in filters and filters['end_date']:
        filtered_df = filtered_df[filtered_df['date'] <= filters['end_date']]
    
    # Filter by type
    if 'type' in filters and filters['type'] and filters['type'] != 'Todos':
        filtered_df = filtered_df[filtered_df['type'] == filters['type']]
    
    # Filter by category
    if 'category' in filters and filters['category'] and filters['category'] != 'Todas':
        filtered_df = filtered_df[filtered_df['category'] == filters['category']]
    
    # Filter by subcategory
    if 'subcategory' in filters and filters['subcategory'] and filters['subcategory'] != 'Todas':
        filtered_df = filtered_df[filtered_df['subcategory'] == filters['subcategory']]
    
    # Filter by payment method
    if 'payment_method' in filters and filters['payment_method'] and filters['payment_method'] != 'Todos':
        filtered_df = filtered_df[filtered_df['payment_method'] == filters['payment_method']]
    
    # Filter by currency
    if 'currency' in filters and filters['currency'] and filters['currency'] != 'Todas':
        filtered_df = filtered_df[filtered_df['currency'] == filters['currency']]
    
    # Filter by fixed expense
    if 'fixed_expense' in filters and filters['fixed_expense'] is not None:
        filtered_df = filtered_df[filtered_df['fixed_expense'] == filters['fixed_expense']]
    
    return filtered_df

def get_categories():
    """Get predefined categories and subcategories"""
    categories = {
        "Ingreso": [
            "Salario", 
            "Freelance", 
            "Inversiones", 
            "Regalos/Préstamos", 
            "Reembolsos", 
            "Otros"
        ],
        "Gasto": [
            "Vivienda", 
            "Alimentación", 
            "Transporte", 
            "Servicios", 
            "Salud", 
            "Educación", 
            "Entretenimiento", 
            "Ropa", 
            "Viajes", 
            "Tecnología", 
            "Regalos", 
            "Impuestos", 
            "Seguros", 
            "Otros"
        ]
    }
    
    return categories
