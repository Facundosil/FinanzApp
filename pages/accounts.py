import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add utils directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.accounts import (
    load_user_accounts, 
    add_account, 
    delete_account, 
    update_account_balance, 
    get_account_types
)

def show_accounts(username):
    """Mostrar la página de cuentas"""
    st.title("Mis Cuentas")
    
    # Cargar las cuentas del usuario
    accounts_df = load_user_accounts(username)
    
    # Crear dos columnas: una para la lista de cuentas y otra para el formulario
    col1, col2 = st.columns([2, 1])
    
    with col1:
        show_accounts_list(username, accounts_df)
    
    with col2:
        show_account_form(username)

def format_currency(value, currency):
    """Formatear valor monetario con símbolo de moneda"""
    if currency == "ARS":
        return f"${value:,.2f} ARS"
    elif currency == "USD":
        return f"${value:,.2f} USD"
    else:
        return f"{value:,.2f} {currency}"

def show_accounts_list(username, accounts_df):
    """Mostrar la lista de cuentas del usuario"""
    st.subheader("Mis Cuentas")
    
    if accounts_df.empty:
        st.info("No tienes cuentas registradas. Crea una nueva cuenta en el formulario de la derecha.")
        return
    
    # Mostrar saldo total por moneda
    st.write("### Saldo Total")
    
    # Agrupar por moneda y sumar los saldos
    total_by_currency = accounts_df.groupby('currency')['balance'].sum().reset_index()
    
    # Crear métricas para cada moneda
    cols = st.columns(len(total_by_currency))
    for i, (_, row) in enumerate(total_by_currency.iterrows()):
        with cols[i]:
            st.metric(
                f"Total en {row['currency']}", 
                format_currency(row['balance'], row['currency'])
            )
    
    # Mostrar lista de cuentas en un formato de tarjetas
    st.write("### Lista de Cuentas")
    
    # Ordenar por tipo y nombre
    accounts_df = accounts_df.sort_values(by=['type', 'name'])
    
    # Convertir tipos de cuentas
    account_types = get_account_types()
    
    # Crear tarjetas para cada cuenta
    for _, account in accounts_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{account['name']}**")
                st.caption(f"Tipo: {account_types.get(account['type'], account['type'])}")
            
            with col2:
                st.write(f"**Saldo:**")
                st.write(format_currency(account['balance'], account['currency']))
            
            with col3:
                # Botones de acción
                if st.button("Editar", key=f"edit_{account['id']}"):
                    st.session_state.editing_account = account.to_dict()
                    st.rerun()
                
                if st.button("Eliminar", key=f"delete_{account['id']}"):
                    # Confirmación antes de eliminar
                    st.session_state.account_to_delete = account['id']
                    st.session_state.account_to_delete_name = account['name']
                    st.rerun()
            
            st.markdown("---")
    
    # Confirmación para eliminar cuenta
    if 'account_to_delete' in st.session_state:
        st.warning(f"¿Estás seguro de que deseas eliminar la cuenta '{st.session_state.account_to_delete_name}'?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí, eliminar"):
                delete_account(username, st.session_state.account_to_delete)
                del st.session_state.account_to_delete
                if 'account_to_delete_name' in st.session_state:
                    del st.session_state.account_to_delete_name
                st.success("Cuenta eliminada con éxito.")
                st.rerun()
        with col2:
            if st.button("Cancelar"):
                del st.session_state.account_to_delete
                if 'account_to_delete_name' in st.session_state:
                    del st.session_state.account_to_delete_name
                st.rerun()

def show_account_form(username):
    """Mostrar formulario para agregar o editar una cuenta"""
    editing = False
    account_data = {
        'id': None,
        'name': '',
        'type': 'bank',
        'balance': 0.0,
        'currency': 'ARS'
    }
    
    if 'editing_account' in st.session_state:
        editing = True
        account_data = st.session_state.editing_account
    
    if editing:
        st.subheader("Editar Cuenta")
    else:
        st.subheader("Agregar Nueva Cuenta")
    
    # Formulario para la cuenta
    with st.form("account_form"):
        name = st.text_input(
            "Nombre de la Cuenta", 
            value=account_data['name']
        )
        
        account_types = get_account_types()
        type_options = list(account_types.keys())
        type_labels = list(account_types.values())
        
        type_index = 0
        if account_data['type'] in type_options:
            type_index = type_options.index(account_data['type'])
        
        account_type = st.selectbox(
            "Tipo de Cuenta",
            options=type_options,
            format_func=lambda x: account_types.get(x, x),
            index=type_index
        )
        
        balance = st.number_input(
            "Saldo Inicial",
            min_value=0.0,
            value=float(account_data['balance'] if editing else 0.0),
            step=100.0
        )
        
        currency = st.selectbox(
            "Moneda",
            options=["ARS", "USD"],
            index=0 if account_data['currency'] == 'ARS' else 1
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Guardar")
        with col2:
            cancel_button = st.form_submit_button("Cancelar")
        
        if submit_button:
            if not name:
                st.error("Por favor ingresa un nombre para la cuenta.")
            else:
                # Preparar datos de la cuenta
                new_account = {
                    'id': account_data['id'],
                    'name': name,
                    'type': account_type,
                    'balance': float(balance),  # Asegurar que sea float
                    'currency': currency
                }
                
                # Guardar la cuenta
                add_account(username, new_account)
                
                if editing:
                    st.success("Cuenta actualizada correctamente.")
                    del st.session_state.editing_account
                else:
                    st.success("Cuenta agregada correctamente.")
                
                st.rerun()
        
        if cancel_button:
            if 'editing_account' in st.session_state:
                del st.session_state.editing_account
            st.rerun()
    
    # Funcionalidades adicionales
    if not editing:
        st.write("### Consejos")
        st.info("""
        - Puedes crear múltiples cuentas para diferentes propósitos.
        - El saldo total se calcula automáticamente por moneda.
        - Las transacciones afectarán al saldo de la cuenta que selecciones.
        """)