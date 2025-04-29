import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
from utils.data_handler import (
    load_user_data, save_transaction, delete_transaction, 
    get_transaction_by_id, get_categories, filter_transactions
)
from utils.currency_api import get_dollar_rate, get_dollar_rate_details
from utils.installment_calculator import calculate_installment_payments
from utils.auto_categorize import suggest_transaction_details
from utils.accounts import load_user_accounts


def display_dollar_rate_info(amount=None, conversion_type="all"):
    """
    Muestra información sobre la cotización actual del dólar (oficial, tarjeta y blue)
    
    Args:
        amount: Monto en dólares para mostrar conversión (opcional)
        conversion_type: Tipo de conversión a mostrar: "official", "card", "blue", o "all"
    """
    # Obtener detalles actualizados de la cotización del dólar
    dollar_details = get_dollar_rate_details()
    dollar_rate = dollar_details['rate']  # Dólar tarjeta
    official_rate = dollar_details['official_rate']
    blue_rate = dollar_details.get('blue_rate', 0)
    
    # Mostrar información detallada sobre la cotización
    info_message = f"""
    💵 **Cotizaciones del Dólar:**
    * **Dólar Oficial:** ${official_rate:.2f} ARS
    * **Dólar Tarjeta:** ${dollar_rate:.2f} ARS (Oficial + {dollar_details['impuesto_pais_pct']:.1f}% + {dollar_details['percepcion_ganancias_pct']:.1f}%)
    * **Dólar Blue:** ${blue_rate:.2f} ARS
    """
    
    st.info(info_message)
    
    # Si se proporciona un monto, mostrar la conversión según el tipo solicitado
    if amount:
        st.write("**Equivalente en Pesos:**")
        
        if conversion_type in ["official", "all"]:
            amount_official = amount * official_rate
            st.write(f"* Oficial: ${amount_official:.2f} ARS")
            
        if conversion_type in ["card", "all"]:
            amount_card = amount * dollar_rate
            st.write(f"* Tarjeta: ${amount_card:.2f} ARS")
            
        if conversion_type in ["blue", "all"] and blue_rate > 0:
            amount_blue = amount * blue_rate
            st.write(f"* Blue: ${amount_blue:.2f} ARS")
    
    # Agregar calculadora de conversión
    st.markdown("---")
    st.markdown("#### Calculadora de Conversión")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        convert_amount = st.number_input("Monto a convertir", min_value=0.0, value=100.0, step=10.0)
    
    with col2:
        conversion_direction = st.selectbox("Dirección", ["USD a ARS", "ARS a USD"])
    
    with col3:
        rate_type = st.selectbox("Tipo de cotización", ["Dólar Oficial", "Dólar Tarjeta", "Dólar Blue"])
    
    # Determinar la tasa a utilizar
    rate_to_use = official_rate
    if rate_type == "Dólar Tarjeta":
        rate_to_use = dollar_rate
    elif rate_type == "Dólar Blue" and blue_rate > 0:
        rate_to_use = blue_rate
    
    # Calcular y mostrar el resultado
    if conversion_direction == "USD a ARS":
        result = convert_amount * rate_to_use
        st.success(f"**{convert_amount:.2f} USD = {result:.2f} ARS** (usando {rate_type})")
    else:
        if rate_to_use > 0:
            result = convert_amount / rate_to_use
            st.success(f"**{convert_amount:.2f} ARS = {result:.2f} USD** (usando {rate_type})")
        else:
            st.error("No se puede convertir porque la cotización es 0.")
    
    return dollar_rate

def show_transactions(username):
    """Mostrar la página de transacciones"""
    st.title("Transacciones")
    
    # Mostrar widget de cotización del dólar en modo compacto
    with st.expander("💵 Ver cotización actual del dólar", expanded=False):
        # Obtener detalles de la cotización
        dollar_details = get_dollar_rate_details()
        
        # Formatear datos
        dollar_rate = dollar_details['rate']  # Dólar tarjeta
        official_rate = dollar_details['official_rate']
        blue_rate = dollar_details.get('blue_rate', 0)  # Dólar blue
        impuesto_pais = dollar_details['impuesto_pais_pct']
        percepcion_ganancias = dollar_details['percepcion_ganancias_pct']
        timestamp = datetime.fromisoformat(dollar_details['timestamp'])
        source = dollar_details['source']
        
        # Fecha y hora formateada
        updated_time = timestamp.strftime("%d/%m/%Y %H:%M")
        
        # Contenedor principal
        st.markdown("""
        <div style="border: 1px solid #DDDDDD; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; margin-bottom: 15px;">Cotización Actual del Dólar</h3>
        """, unsafe_allow_html=True)
        
        # Mostrar cotizaciones en tres columnas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="text-align: center;">
                <h4>Dólar Oficial</h4>
                <h2>${official_rate:.2f} ARS</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center;">
                <h4>Dólar Tarjeta</h4>
                <h2>${dollar_rate:.2f} ARS</h2>
                <p style="font-size: 0.8em; margin-top: 0;">
                    (Oficial + Imp. PAIS {impuesto_pais:.1f}% + Percepción {percepcion_ganancias:.1f}%)
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div style="text-align: center;">
                <h4>Dólar Blue</h4>
                <h2>${blue_rate:.2f} ARS</h2>
            </div>
            """, unsafe_allow_html=True)
    
    # Cargar datos del usuario
    df = load_user_data(username)
    
    # Selección de pestañas
    tab1, tab2, tab3 = st.tabs(["Ver Transacciones", "Registrar Ingreso", "Registrar Gasto"])
    
    with tab1:
        show_transactions_list(username, df)
    
    with tab2:
        show_income_form(username)
    
    with tab3:
        show_expense_form(username)

def show_transactions_list(username, df):
    """Show list of transactions with filtering options"""
    # Filter section
    st.subheader("Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Date filter
        start_date = st.date_input("Desde fecha", 
                                    value=None,
                                    format="YYYY-MM-DD")
        
        # Type filter
        transaction_type = st.selectbox(
            "Tipo",
            options=["Todos", "Ingreso", "Gasto"],
            index=0
        )
        
        # Payment method filter (for expenses)
        payment_method = st.selectbox(
            "Método de pago",
            options=["Todos", "Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia", "Débito Automático", "Otro"],
            index=0
        )
    
    with col2:
        # End date filter
        end_date = st.date_input("Hasta fecha", 
                                  value=None,
                                  format="YYYY-MM-DD")
        
        # Category filter
        all_categories = get_categories()
        flat_categories = ["Todas"] + list(all_categories.get("Ingreso", [])) + list(all_categories.get("Gasto", []))
        
        category = st.selectbox(
            "Categoría",
            options=flat_categories,
            index=0
        )
        
        # Fixed expense filter
        fixed_expense = st.selectbox(
            "Gasto Fijo",
            options=[None, True, False],
            format_func=lambda x: "Todos" if x is None else ("Sí" if x else "No"),
            index=0
        )
    
    with col3:
        # Currency filter
        currency = st.selectbox(
            "Moneda",
            options=["Todas", "ARS", "USD"],
            index=0
        )
        
        # Apply filters button
        st.write("") # Spacing
        st.write("") # Spacing
        filter_button = st.button("Aplicar Filtros", use_container_width=True)
    
    # Convert dates to string format for filtering
    filters = {
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
        'type': transaction_type if transaction_type != "Todos" else None,
        'category': category if category != "Todas" else None,
        'payment_method': payment_method if payment_method != "Todos" else None,
        'currency': currency if currency != "Todas" else None,
        'fixed_expense': fixed_expense
    }
    
    # Apply filters
    if filter_button or 'filtered_df' not in st.session_state:
        filtered_df = filter_transactions(df, filters)
        st.session_state.filtered_df = filtered_df
    else:
        filtered_df = st.session_state.filtered_df
    
    # Display results
    st.subheader("Resultados")
    
    if filtered_df.empty:
        st.info("No hay transacciones que coincidan con los filtros seleccionados.")
        return
    
    # Format data for display
    display_df = filtered_df.copy()
    
    # Format the amount with currency
    display_df['monto'] = display_df.apply(
        lambda x: f"${x['amount']:.2f} {x['currency']}", axis=1
    )
    
    # Format installments if applicable
    display_df['cuotas'] = display_df.apply(
        lambda x: f"{x['installments_paid']}/{x['installments_total']}" 
        if pd.notna(x['installments_total']) and x['installments_total'] > 1 
        else "-", 
        axis=1
    )
    
    # Indicate fixed expenses
    display_df['fijo'] = display_df['fixed_expense'].map({True: "Sí", False: "No"})
    
    # Select columns for display
    display_columns = [
        'date', 'type', 'category', 'description', 
        'monto', 'payment_method', 'fijo', 'cuotas'
    ]
    
    # Rename columns for display
    column_names = {
        'date': 'Fecha',
        'type': 'Tipo',
        'category': 'Categoría',
        'description': 'Descripción',
        'monto': 'Monto',
        'payment_method': 'Método de Pago',
        'fijo': 'Gasto Fijo',
        'cuotas': 'Cuotas'
    }
    
    # Preparar el dataframe para mostrar como tabla interactiva
    display_df = display_df.sort_values('date', ascending=False).copy()
    
    # Añadir columna de acciones vacía (se llenará con botones)
    display_df['acciones'] = ''
    
    # Configuración de columnas para la tabla
    column_config = {
        'date': st.column_config.TextColumn("Fecha"),
        'type': st.column_config.TextColumn("Tipo"),
        'category': st.column_config.TextColumn("Categoría"),
        'description': st.column_config.TextColumn("Descripción"),
        'monto': st.column_config.TextColumn("Monto"),
        'payment_method': st.column_config.TextColumn("Método de Pago"),
        'fijo': st.column_config.TextColumn("Gasto Fijo"),
        'cuotas': st.column_config.TextColumn("Cuotas"),
        'acciones': st.column_config.TextColumn("Acciones")
    }
    
    # Mostrar la tabla
    st.dataframe(
        display_df[['date', 'type', 'category', 'description', 'monto', 'payment_method', 'fijo', 'cuotas', 'acciones']], 
        column_config=column_config,
        hide_index=True
    )
    
    # Botones de edición y eliminación bajo la tabla
    st.markdown("### Acciones")
    st.markdown("Selecciona una transacción para editar o eliminar:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_id = st.selectbox("Seleccionar transacción", 
                                options=display_df['id'].tolist(),
                                format_func=lambda x: f"{display_df[display_df['id'] == x]['date'].values[0]} - {display_df[display_df['id'] == x]['description'].values[0]} - {display_df[display_df['id'] == x]['monto'].values[0]}")
    
    with col2:
        if st.button("✏️ Editar transacción", key="edit_selected"):
            st.session_state.editing_transaction = selected_id
            st.rerun()
    
    with col3:
        # Crear una clave única para el estado de confirmación de esta transacción
        confirm_key = "confirm_delete_selected"
        
        # Mostrar botón de eliminar o botones de confirmar/cancelar
        if confirm_key not in st.session_state or not st.session_state[confirm_key]:
            if st.button("🗑️ Eliminar transacción", key="delete_selected"):
                # Activar modo de confirmación
                st.session_state[confirm_key] = True
                st.rerun()
        else:
            col3_1, col3_2 = st.columns(2)
            with col3_1:
                if st.button("✓ Confirmar", key="confirm_selected", help="Confirmar eliminación"):
                    if delete_transaction(username, selected_id):
                        st.success(f"Transacción eliminada correctamente.")
                        # Limpiar el estado de confirmación
                        if confirm_key in st.session_state:
                            del st.session_state[confirm_key]
                        st.rerun()
            with col3_2:
                if st.button("✗ Cancelar", key="cancel_selected", help="Cancelar eliminación"):
                    # Cancelar la eliminación
                    if confirm_key in st.session_state:
                        del st.session_state[confirm_key]
                    st.rerun()

def show_income_form(username):
    """Mostrar formulario para agregar o editar un ingreso"""
    
    # Initialize form values
    transaction_data = {
        'id': None,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'type': 'Ingreso',  # Tipo fijo: Ingreso
        'category': None,
        'subcategory': None,
        'description': '',
        'amount': 0.0,
        'currency': 'ARS',
        'exchange_rate': get_dollar_rate_details()["rate"],
        'amount_pesos': 0.0,
        'payment_method': None,
        'fixed_expense': False,
        'installments_total': 1,
        'installments_paid': 0,
        'account_id': None
    }
    
    # Cargar las cuentas del usuario
    accounts_df = load_user_accounts(username)
    
    # If editing, load transaction data
    editing = False
    if 'editing_transaction' in st.session_state:
        transaction_id = st.session_state.editing_transaction
        existing_transaction = get_transaction_by_id(username, transaction_id)
        
        if existing_transaction and existing_transaction['type'] == 'Ingreso':
            transaction_data = existing_transaction
            editing = True
            st.subheader(f"Editar Ingreso #{transaction_id}")
        else:
            st.subheader("Registrar Nuevo Ingreso")
    else:
        st.subheader("Registrar Nuevo Ingreso")
    
    # Transaction form
    with st.form("income_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Date
            transaction_date = st.date_input(
                "Fecha",
                value=pd.to_datetime(transaction_data['date']) if transaction_data['date'] else datetime.now(),
                format="YYYY-MM-DD"
            )
            
            # Tipo es siempre 'Ingreso'
            transaction_type = 'Ingreso'
            
            # Categories based on type
            categories = get_categories()
            category_options = categories.get(transaction_type, [])
            
            category = st.selectbox(
                "Categoría",
                options=category_options,
                index=category_options.index(transaction_data['category']) if transaction_data['category'] in category_options else 0
            )
            
            # Description
            description = st.text_input(
                "Descripción",
                value=transaction_data['description']
            )
        
        with col2:
            # Amount
            amount = st.number_input(
                "Monto",
                min_value=0.01,
                value=float(transaction_data['amount']) if transaction_data['amount'] else 0.01,
                step=0.01
            )
            
            # Currency
            currency = st.selectbox(
                "Moneda",
                options=["ARS", "USD"],
                index=0 if transaction_data['currency'] == 'ARS' else 1
            )
            
            # Show current dollar rate for reference
            if currency == "USD":
                # Usar la función para mostrar información del dólar y el monto convertido
                dollar_rate = display_dollar_rate_info(amount)
                
            # Selector de cuenta
            if not accounts_df.empty:
                account_options = [(account['id'], account['name']) for _, account in accounts_df.iterrows()]
                account_ids = [account[0] for account in account_options]
                account_names = [account[1] for account in account_options]
                
                selected_account_index = 0
                if transaction_data.get('account_id') in account_ids:
                    selected_account_index = account_ids.index(transaction_data['account_id'])
                
                account_id = st.selectbox(
                    "Cuenta a la que ingresa el dinero",
                    options=account_ids,
                    format_func=lambda x: account_names[account_ids.index(x)],
                    index=selected_account_index
                )
            else:
                st.warning("No tienes cuentas disponibles. Por favor crea una cuenta primero.")
                account_id = None
                
            # Fields no aplicables para ingresos
            payment_method = None
            fixed_expense = False
            installments_total = 1
            installments_paid = 0
            
            # Buttons
            submit_button = st.form_submit_button("Guardar")
            cancel_button = st.form_submit_button("Cancelar")
        
        # Process form submission
        if submit_button:
            # Prepare transaction data
            new_transaction = {
                'id': transaction_data['id'],
                'date': transaction_date.strftime('%Y-%m-%d'),
                'type': transaction_type,
                'category': category,
                'subcategory': '',  # Not used in this version
                'description': description,
                'amount': amount,
                'currency': currency,
                'exchange_rate': get_dollar_rate_details()['rate'] if currency == 'USD' else 1.0,
                'amount_pesos': amount * get_dollar_rate_details()['rate'] if currency == 'USD' else amount,
                'payment_method': payment_method,
                'fixed_expense': fixed_expense,
                'installments_total': installments_total,
                'installments_paid': installments_paid,
                'account_id': account_id
            }
            
            # Save transaction
            if save_transaction(username, new_transaction):
                if editing:
                    st.success("Ingreso actualizado correctamente.")
                else:
                    st.success("Ingreso registrado correctamente.")
                
                # Clear editing state
                if 'editing_transaction' in st.session_state:
                    del st.session_state.editing_transaction
                
                st.rerun()
        
        if cancel_button:
            if 'editing_transaction' in st.session_state:
                del st.session_state.editing_transaction
            st.rerun()
            
    # Botón cancelar fuera del formulario
    if st.button("Cancelar", key="cancel_income_form"):
        if 'editing_transaction' in st.session_state:
            del st.session_state.editing_transaction
        st.rerun()

def show_expense_form(username):
    """Mostrar formulario para agregar o editar un gasto"""
    
    # Initialize form values
    transaction_data = {
        'id': None,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'type': 'Gasto',  # Tipo fijo: Gasto
        'category': None,
        'subcategory': None,
        'description': '',
        'amount': 0.0,
        'currency': 'ARS',
        'exchange_rate': get_dollar_rate_details()['rate'],
        'amount_pesos': 0.0,
        'payment_method': 'Efectivo',
        'fixed_expense': False,
        'installments_total': 1,
        'installments_paid': 0,
        'account_id': None
    }
    
    # Cargar las cuentas del usuario
    accounts_df = load_user_accounts(username)
    
    # Aplicar sugerencias si el usuario lo solicitó
    if 'apply_suggestions' in st.session_state and st.session_state.apply_suggestions:
        if 'suggested_category' in st.session_state:
            transaction_data['category'] = st.session_state.suggested_category
        if 'suggested_payment_method' in st.session_state:
            transaction_data['payment_method'] = st.session_state.suggested_payment_method
        if 'suggested_fixed_expense' in st.session_state:
            transaction_data['fixed_expense'] = st.session_state.suggested_fixed_expense
        
        # Limpiar las sugerencias después de aplicarlas
        st.session_state.pop('apply_suggestions', None)
        st.session_state.pop('suggested_category', None)
        st.session_state.pop('suggested_payment_method', None)
        st.session_state.pop('suggested_fixed_expense', None)
    
    # If editing, load transaction data
    editing = False
    if 'editing_transaction' in st.session_state:
        transaction_id = st.session_state.editing_transaction
        existing_transaction = get_transaction_by_id(username, transaction_id)
        
        if existing_transaction and existing_transaction['type'] == 'Gasto':
            transaction_data = existing_transaction
            editing = True
            st.subheader(f"Editar Gasto #{transaction_id}")
        else:
            st.subheader("Registrar Nuevo Gasto")
    else:
        st.subheader("Registrar Nuevo Gasto")
    
    # Si no estamos editando, permitir sugerencias basadas en la descripción
    if not editing and 'temp_description' in st.session_state and len(st.session_state.temp_description) > 3:
        col_suggest, col_apply = st.columns(2)
        
        with col_suggest:
            if st.button("📋 Sugerir categoría", key="suggest_category"):
                df = load_user_data(username)
                if not df.empty and len(df) > 0:
                    with st.spinner("Analizando transacciones similares..."):
                        suggestions = suggest_transaction_details(username, df, st.session_state.temp_description)
                        
                        if suggestions and suggestions.get('confidence', 0) > 0.3:
                            st.session_state.suggested_category = suggestions.get('category')
                            st.session_state.suggested_payment_method = suggestions.get('payment_method')
                            st.session_state.suggested_fixed_expense = suggestions.get('fixed_expense')
                            
                            confidence_percentage = int(suggestions.get('confidence', 0) * 100)
                            
                            st.success(f"Sugerencias basadas en transacciones similares ({confidence_percentage}% de confianza):")
                            st.markdown(f"**Categoría:** {suggestions.get('category')}")
                            if suggestions.get('payment_method'):
                                st.markdown(f"**Método de pago:** {suggestions.get('payment_method')}")
                            st.markdown(f"**Gasto fijo:** {'Sí' if suggestions.get('fixed_expense') else 'No'}")
                            
                            st.session_state.show_apply_suggestion = True
                        else:
                            st.info("No se encontraron transacciones similares para sugerir categorías.")
        
        if 'show_apply_suggestion' in st.session_state and st.session_state.show_apply_suggestion:
            with col_apply:
                if st.button("✅ Aplicar sugerencias", key="apply_suggestions"):
                    st.session_state.apply_suggestions = True
                    st.rerun()
                
    # Transaction form
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Date
            transaction_date = st.date_input(
                "Fecha",
                value=pd.to_datetime(transaction_data['date']) if transaction_data['date'] else datetime.now(),
                format="YYYY-MM-DD"
            )
            
            # Tipo es siempre 'Gasto'
            transaction_type = 'Gasto'
            
            # Categories based on type
            categories = get_categories()
            category_options = categories.get(transaction_type, [])
            
            category = st.selectbox(
                "Categoría",
                options=category_options,
                index=category_options.index(transaction_data['category']) if transaction_data['category'] in category_options else 0
            )
            
            # Description with auto-categorization
            description = st.text_input(
                "Descripción",
                value=transaction_data['description'],
                key="expense_description"
            )
            # Guardamos la descripción para su uso fuera del formulario
            st.session_state.temp_description = description
            
            # Amount
            amount = st.number_input(
                "Monto",
                min_value=0.01,
                value=float(transaction_data['amount']) if transaction_data['amount'] else 0.01,
                step=0.01
            )
            
            # Currency
            currency = st.selectbox(
                "Moneda",
                options=["ARS", "USD"],
                index=0 if transaction_data['currency'] == 'ARS' else 1
            )
        
        with col2:
            # Payment method
            payment_method = st.selectbox(
                "Método de Pago",
                options=["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia", "Débito Automático", "Otro"],
                index=0 if transaction_data['payment_method'] is None else ["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia", "Débito Automático", "Otro"].index(transaction_data['payment_method'])
            )
            
            # Fixed expense
            fixed_expense = st.checkbox(
                "Gasto Fijo",
                value=transaction_data['fixed_expense']
            )
            
            # Installments for credit card
            show_installments = payment_method == "Tarjeta de Crédito"
            
            if show_installments:
                installments_total = st.number_input(
                    "Número Total de Cuotas",
                    min_value=1,
                    max_value=60,
                    value=int(transaction_data['installments_total']) if transaction_data['installments_total'] else 1,
                    step=1
                )
                
                if editing:
                    installments_paid = st.number_input(
                        "Cuotas Pagadas",
                        min_value=0,
                        max_value=installments_total,
                        value=int(transaction_data['installments_paid']) if transaction_data['installments_paid'] else 0,
                        step=1
                    )
                else:
                    installments_paid = 0
            else:
                installments_total = 1
                installments_paid = 0
            
            # Show current dollar rate for reference
            if currency == "USD":
                # Usar la función para mostrar información del dólar y el monto convertido
                dollar_rate = display_dollar_rate_info(amount)
            
            # Selector de cuenta
            if not accounts_df.empty:
                account_options = [(account['id'], account['name']) for _, account in accounts_df.iterrows()]
                account_ids = [account[0] for account in account_options]
                account_names = [account[1] for account in account_options]
                
                selected_account_index = 0
                if transaction_data.get('account_id') in account_ids:
                    selected_account_index = account_ids.index(transaction_data['account_id'])
                
                account_id = st.selectbox(
                    "Cuenta de la que sale el dinero",
                    options=account_ids,
                    format_func=lambda x: account_names[account_ids.index(x)],
                    index=selected_account_index
                )
            else:
                st.warning("No tienes cuentas disponibles. Por favor crea una cuenta primero.")
                account_id = None
            
            # Buttons
            submit_button = st.form_submit_button("Guardar")
            cancel_button = st.form_submit_button("Cancelar")
        
        # Process form submission
        if submit_button:
            # Prepare transaction data
            new_transaction = {
                'id': transaction_data['id'],
                'date': transaction_date.strftime('%Y-%m-%d'),
                'type': transaction_type,
                'category': category,
                'subcategory': '',  # Not used in this version
                'description': description,
                'amount': amount,
                'currency': currency,
                'exchange_rate': get_dollar_rate_details()['rate'] if currency == 'USD' else 1.0,
                'amount_pesos': amount * get_dollar_rate_details()['rate'] if currency == 'USD' else amount,
                'payment_method': payment_method,
                'fixed_expense': fixed_expense,
                'installments_total': installments_total,
                'installments_paid': installments_paid,
                'account_id': account_id
            }
            
            # Save transaction
            if save_transaction(username, new_transaction):
                if editing:
                    st.success("Gasto actualizado correctamente.")
                else:
                    st.success("Gasto registrado correctamente.")
                
                # Clear editing state
                if 'editing_transaction' in st.session_state:
                    del st.session_state.editing_transaction
                
                st.rerun()
        
        if cancel_button:
            if 'editing_transaction' in st.session_state:
                del st.session_state.editing_transaction
            st.rerun()
            
    # Botón cancelar fuera del formulario
    if st.button("Cancelar", key="cancel_expense_form"):
        if 'editing_transaction' in st.session_state:
            del st.session_state.editing_transaction
        st.rerun()
    
    # Si estamos editando y la transacción tiene cuotas, mostrar detalles de las cuotas
    if editing and transaction_data['installments_total'] > 1:
        st.subheader("Detalle de Cuotas")
        
        installments_df = calculate_installment_payments(
            transaction_data, 
            st.session_state.dollar_rate
        )
        
        st.dataframe(
            installments_df,
            column_config={
                'installment_number': st.column_config.NumberColumn("Cuota #"),
                'date': st.column_config.TextColumn("Fecha de Pago"),
                'amount': st.column_config.NumberColumn("Monto", format="$%.2f"),
                'currency': st.column_config.TextColumn("Moneda"),
                'amount_pesos': st.column_config.NumberColumn("Monto en Pesos", format="$%.2f"),
                'paid': st.column_config.CheckboxColumn("Pagada")
            },
            hide_index=True
        )
