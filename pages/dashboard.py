import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import calendar
import sys
import os
from utils.data_handler import load_user_data
from utils.installment_calculator import get_upcoming_installments
from utils.advanced_analytics import (
    get_spending_forecast, detect_unusual_spending, 
    calculate_savings_projection, analyze_expense_trends
)
from utils.financial_goals import load_user_goals, calculate_goal_progress
from utils.currency_api import get_dollar_rate_details, get_historical_rates

def show_dollar_rate_widget():
    """Mostrar widget con la cotización actual del dólar"""
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
    
    with st.expander("💵 Cotización del Dólar", expanded=True):
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
            
        # Agregar una calculadora de conversión
        st.markdown("""
        <hr style="margin-top: 20px; margin-bottom: 20px;">
        <h4 style="margin-bottom: 10px;">Calculadora de Conversión</h4>
        """, unsafe_allow_html=True)
        
        # Input para monto a convertir
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        
        with col1:
            convert_amount = st.number_input("Monto", min_value=0.01, value=100.0, step=10.0)
        
        with col2:
            convert_direction = st.radio("", ["USD → ARS", "ARS → USD"])
        
        with col3:
            rate_type = st.radio("Tipo", ["Oficial", "Tarjeta", "Blue"])
            
            # Determinar la tasa a utilizar
            if rate_type == "Oficial":
                rate_to_use = official_rate
            elif rate_type == "Tarjeta":
                rate_to_use = dollar_rate
            else:  # Blue
                rate_to_use = blue_rate
        
        with col4:
            if convert_direction == "USD → ARS" and rate_to_use > 0:
                result = convert_amount * rate_to_use
                st.markdown(f"<div style='text-align: center; padding-top: 25px;'><b>${convert_amount:.2f} USD = ${result:.2f} ARS</b></div>", unsafe_allow_html=True)
            elif rate_to_use > 0:
                result = convert_amount / rate_to_use
                st.markdown(f"<div style='text-align: center; padding-top: 25px;'><b>${convert_amount:.2f} ARS = ${result:.2f} USD</b></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align: center; padding-top: 25px; color: red;'><b>No se puede convertir (cotización no disponible)</b></div>", unsafe_allow_html=True)
        
        # Mostrar fecha de actualización y fuente
        st.markdown(f"""
        <div style="text-align: right; font-size: 0.8em; color: #888888; margin-top: 15px;">
            <p>Actualizado: {updated_time} | Fuente: {source}</p>
        </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar tendencia histórica si hay datos
        try:
            historical_rates = get_historical_rates(days=10)
            
            if not historical_rates.empty and len(historical_rates) > 1:
                st.markdown("### Tendencia Histórica")
                
                # Crear gráfico de líneas para la tendencia
                fig, ax = plt.subplots(figsize=(10, 4))
                
                ax.plot(historical_rates['date'], historical_rates['official_rate'], 
                        marker='o', linestyle='-', color='blue', label='Dólar Oficial')
                ax.plot(historical_rates['date'], historical_rates['card_rate'], 
                        marker='o', linestyle='-', color='red', label='Dólar Tarjeta')
                
                # Mostrar dólar blue si está disponible
                if 'blue_rate' in historical_rates.columns and not historical_rates['blue_rate'].isnull().all():
                    ax.plot(historical_rates['date'], historical_rates['blue_rate'], 
                           marker='o', linestyle='-', color='green', label='Dólar Blue')
                
                # Configurar el gráfico
                ax.set_ylabel('Cotización (ARS)')
                ax.set_xlabel('')
                ax.legend()
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Formatear fechas en el eje x
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                st.pyplot(fig)
                
                # Variación en el período
                if len(historical_rates) > 1:
                    first_official = historical_rates['official_rate'].iloc[0]
                    last_official = historical_rates['official_rate'].iloc[-1]
                    first_card = historical_rates['card_rate'].iloc[0]
                    last_card = historical_rates['card_rate'].iloc[-1]
                    
                    official_change_pct = ((last_official - first_official) / first_official) * 100
                    card_change_pct = ((last_card - first_card) / first_card) * 100
                    
                    # Comprobar si hay datos de dólar blue
                    has_blue = 'blue_rate' in historical_rates.columns and not historical_rates['blue_rate'].isnull().all()
                    
                    if has_blue:
                        # 3 columnas para mostrar todas las variaciones
                        col1, col2, col3 = st.columns(3)
                        
                        # Calcular variación del dólar blue
                        first_blue = historical_rates['blue_rate'].iloc[0]
                        last_blue = historical_rates['blue_rate'].iloc[-1]
                        blue_change_pct = ((last_blue - first_blue) / first_blue) * 100
                    else:
                        # 2 columnas si no hay dólar blue
                        col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Variación Dólar Oficial", 
                                 f"{official_change_pct:+.2f}%", 
                                 delta=f"${last_official - first_official:.2f}")
                    
                    with col2:
                        st.metric("Variación Dólar Tarjeta", 
                                 f"{card_change_pct:+.2f}%", 
                                 delta=f"${last_card - first_card:.2f}")
                    
                    if has_blue:
                        with col3:
                            st.metric("Variación Dólar Blue", 
                                     f"{blue_change_pct:+.2f}%", 
                                     delta=f"${last_blue - first_blue:.2f}")
        except Exception as e:
            st.warning(f"No se pudo cargar el histórico de cotizaciones: {e}")


def show_dashboard(username):
    """Mostrar el dashboard principal para el usuario"""
    st.title("Dashboard")
    
    # Mostrar widget de cotización del dólar
    show_dollar_rate_widget()
    
    # Cargar datos del usuario
    df = load_user_data(username)
    
    if df.empty:
        st.info("No hay datos de transacciones. Comienza agregando transacciones en la página 'Transacciones'.")
        return
    
    # Convertir fecha a datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Obtener datos del mes actual
    today = datetime.now()
    first_day_current_month = datetime(today.year, today.month, 1)
    last_day_current_month = datetime(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
    
    current_month_data = df[(df['date'] >= first_day_current_month) & (df['date'] <= last_day_current_month)]
    
    # Calculate summary metrics
    col1, col2, col3 = st.columns(3)
    
    # Total balance (all time)
    total_income = df[df['type'] == 'Ingreso']['amount_pesos'].sum()
    total_expense = df[df['type'] == 'Gasto']['amount_pesos'].sum()
    total_balance = total_income - total_expense
    
    with col1:
        st.metric("Balance Total", f"${total_balance:.2f}")
    
    # Current month income/expenses
    current_month_income = current_month_data[current_month_data['type'] == 'Ingreso']['amount_pesos'].sum()
    current_month_expense = current_month_data[current_month_data['type'] == 'Gasto']['amount_pesos'].sum()
    current_month_balance = current_month_income - current_month_expense
    
    with col2:
        st.metric("Ingresos del Mes", f"${current_month_income:.2f}")
    
    with col3:
        st.metric("Gastos del Mes", f"${current_month_expense:.2f}")
    
    # Monthly trend chart
    st.subheader("Tendencia Mensual")
    
    # Group by month and calculate totals
    df['month'] = df['date'].dt.strftime('%Y-%m')
    monthly_totals = df.groupby(['month', 'type'])['amount_pesos'].sum().unstack().fillna(0)
    
    if 'Ingreso' not in monthly_totals.columns:
        monthly_totals['Ingreso'] = 0
    if 'Gasto' not in monthly_totals.columns:
        monthly_totals['Gasto'] = 0
    
    monthly_totals['Balance'] = monthly_totals['Ingreso'] - monthly_totals['Gasto']
    
    # Sort by date
    monthly_totals = monthly_totals.sort_index()
    
    # Show last 6 months
    last_n_months = 6
    if len(monthly_totals) > last_n_months:
        monthly_totals = monthly_totals.iloc[-last_n_months:]
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    monthly_totals['Ingreso'].plot(kind='bar', color='green', ax=ax, position=0, width=0.25, label='Ingresos')
    monthly_totals['Gasto'].plot(kind='bar', color='red', ax=ax, position=1, width=0.25, label='Gastos')
    monthly_totals['Balance'].plot(kind='line', color='blue', marker='o', ax=ax, label='Balance')
    
    ax.set_xlabel('Mes')
    ax.set_ylabel('Monto (ARS)')
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig)
    
    # Expenses by category for current month
    st.subheader("Gastos por Categoría (Mes Actual)")
    
    if current_month_data[current_month_data['type'] == 'Gasto'].empty:
        st.info("No hay gastos registrados en el mes actual.")
    else:
        expenses_by_category = current_month_data[current_month_data['type'] == 'Gasto'].groupby('category')['amount_pesos'].sum()
        
        fig, ax = plt.subplots(figsize=(8, 8))
        expenses_by_category.plot(kind='pie', autopct='%1.1f%%', ax=ax)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.tight_layout()
        
        st.pyplot(fig)
    
    # Upcoming installment payments
    st.subheader("Próximos Pagos en Cuotas")
    
    upcoming_installments = get_upcoming_installments(username, df)
    
    if upcoming_installments.empty:
        st.info("No hay pagos en cuotas programados para los próximos meses.")
    else:
        # Format display and show
        upcoming_installments['amount_display'] = upcoming_installments.apply(
            lambda x: f"${x['amount']:.2f} {x['currency']}", axis=1)
        
        upcoming_installments['cuota'] = upcoming_installments.apply(
            lambda x: f"{x['installment_number']}/{x['total_installments']}", axis=1)
        
        # Display as a table
        st.dataframe(
            upcoming_installments[['payment_date', 'description', 'cuota', 'amount_display']],
            column_config={
                'payment_date': st.column_config.TextColumn("Fecha"),
                'description': st.column_config.TextColumn("Descripción"),
                'cuota': st.column_config.TextColumn("Cuota"),
                'amount_display': st.column_config.TextColumn("Monto")
            },
            hide_index=True
        )
    
    # Panel de Análisis Avanzado
    st.markdown("---")
    st.subheader("📊 Panel de Análisis Avanzado")
    
    # Crear pestañas para cada tipo de análisis
    tab1, tab2, tab3, tab4 = st.tabs([
        "Detección de Gastos Inusuales", 
        "Proyección de Gastos", 
        "Tendencias de Gastos",
        "Simulador de Ahorros"
    ])
    
    with tab1:
        st.markdown("### Detección de Gastos Inusuales")
        
        # Detectar gastos inusuales
        unusual_spending = detect_unusual_spending(df, threshold_factor=1.5)
        
        if unusual_spending.empty:
            st.info("No se detectaron gastos inusuales en el mes actual.")
        else:
            st.markdown("Las siguientes categorías tienen gastos inusualmente altos este mes:")
            
            for _, row in unusual_spending.iterrows():
                category = row['category']
                current = row['current_amount']
                avg = row['avg_amount']
                percent = row['percent_increase']
                
                # Crear un contenedor con borde para cada alerta
                with st.container():
                    st.markdown(f"""
                    <div style="border-left: 4px solid #FF5252; padding-left: 10px; margin-bottom: 10px;">
                        <h4 style="margin-bottom: 0;">{category}</h4>
                        <p>Gasto actual: <b>${current:.2f}</b> | Promedio mensual: <b>${avg:.2f}</b></p>
                        <p>Incremento: <b style="color: #FF5252;">+{percent:.1f}%</b></p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Proyección de Gastos para los Próximos Meses")
        
        # Obtener la proyección
        spending_forecast = get_spending_forecast(df, months_ahead=3)
        
        if spending_forecast.empty:
            st.info("No hay suficientes datos para realizar una proyección de gastos.")
        else:
            # Agrupar por mes para obtener el total proyectado
            monthly_forecast = spending_forecast.groupby('month')['amount_pesos'].sum()
            
            # Crear gráfico de barras para la proyección total
            fig, ax = plt.subplots(figsize=(10, 5))
            monthly_forecast.plot(kind='bar', color='purple', ax=ax)
            
            ax.set_xlabel('Mes')
            ax.set_ylabel('Gasto Proyectado (ARS)')
            ax.set_title('Proyección de Gastos Totales')
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            st.pyplot(fig)
            
            # Mostrar desglose por categoría
            st.markdown("#### Desglose por Categoría")
            
            # Pivotear para mostrar categorías por mes
            pivot_forecast = spending_forecast.pivot_table(
                index='category', 
                columns='month', 
                values='amount_pesos', 
                aggfunc='sum'
            ).fillna(0)
            
            # Formatear como tabla
            formatted_forecast = pivot_forecast.copy()
            for col in formatted_forecast.columns:
                formatted_forecast[col] = formatted_forecast[col].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(formatted_forecast)
    
    with tab3:
        st.markdown("### Tendencias de Gastos por Categoría")
        
        # Obtener análisis de tendencias
        trends = analyze_expense_trends(df)
        
        if not trends:
            st.info("No hay suficientes datos para analizar tendencias.")
        else:
            # Categorías con tendencia al alza
            st.markdown("#### Categorías con tendencia al alza")
            if not trends['increasing']:
                st.info("No se detectaron categorías con tendencia significativa al alza.")
            else:
                for category, data in trends['increasing'].items():
                    pct = data['monthly_change_percent']
                    avg = data['avg_monthly_amount']
                    strength = data['strength']
                    
                    strength_color = "#FFA726" if strength == "moderate" else "#F44336"
                    
                    st.markdown(f"""
                    <div style="border-left: 4px solid {strength_color}; padding-left: 10px; margin-bottom: 10px;">
                        <h4 style="margin-bottom: 0;">{category}</h4>
                        <p>Gasto promedio: <b>${avg:.2f}</b> | Tendencia: <b style="color: {strength_color};">+{pct:.1f}% mensual</b></p>
                        <p>Intensidad: <b>{strength.capitalize()}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Categorías con tendencia a la baja
            st.markdown("#### Categorías con tendencia a la baja")
            if not trends['decreasing']:
                st.info("No se detectaron categorías con tendencia significativa a la baja.")
            else:
                for category, data in trends['decreasing'].items():
                    pct = abs(data['monthly_change_percent'])
                    avg = data['avg_monthly_amount']
                    strength = data['strength']
                    
                    strength_color = "#4CAF50" if strength == "strong" else "#8BC34A"
                    
                    st.markdown(f"""
                    <div style="border-left: 4px solid {strength_color}; padding-left: 10px; margin-bottom: 10px;">
                        <h4 style="margin-bottom: 0;">{category}</h4>
                        <p>Gasto promedio: <b>${avg:.2f}</b> | Tendencia: <b style="color: {strength_color};">-{pct:.1f}% mensual</b></p>
                        <p>Intensidad: <b>{strength.capitalize()}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### Simulador de Ahorros")
        
        # Input para el objetivo de ahorro mensual
        monthly_saving_target = st.slider(
            "Objetivo de Ahorro Mensual (ARS)",
            min_value=1000,
            max_value=50000,
            value=5000,
            step=1000
        )
        
        # Calcular la proyección de ahorros
        savings_projection = calculate_savings_projection(df, monthly_saving_target)
        
        if not savings_projection or 'possible' not in savings_projection:
            st.info("No hay suficientes datos para realizar una proyección de ahorros.")
        else:
            # Mostrar mensaje principal
            status_color = "#4CAF50" if savings_projection['possible'] else "#F44336"
            st.markdown(f"""
            <div style="border-left: 4px solid {status_color}; padding-left: 10px; margin-bottom: 10px;">
                <h4 style="margin-bottom: 0; color: {status_color};">{savings_projection['message']}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Verificar que las claves existan antes de mostrar métricas
            if 'avg_income' in savings_projection and 'avg_expenses' in savings_projection and 'avg_balance' in savings_projection:
                # Mostrar métricas clave
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Ingreso Mensual Promedio", f"${savings_projection['avg_income']:.2f}")
                
                with col2:
                    st.metric("Gasto Mensual Promedio", f"${savings_projection['avg_expenses']:.2f}")
                
                with col3:
                    st.metric("Balance Mensual Promedio", f"${savings_projection['avg_balance']:.2f}")
            
            # Si se necesita reducir gastos, mostrar esas métricas
            if 'suggested_expense_reduction' in savings_projection and savings_projection['suggested_expense_reduction'] > 0:
                st.markdown("#### Para alcanzar tu objetivo de ahorro:")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Reducción Necesaria", f"${savings_projection['suggested_expense_reduction']:.2f}")
                    st.metric("Nuevo Objetivo de Gastos", f"${savings_projection['new_expense_target']:.2f}")
                
                with col2:
                    st.metric("Reducción Porcentual", f"{savings_projection['reduction_percent']:.1f}%")
                    st.metric("% de Ingresos para Ahorros", f"{savings_projection['savings_percent']:.1f}%")
                
                # Visualizar la distribución
                fig, ax = plt.subplots(figsize=(8, 5))
                
                # Crear datos para el gráfico
                labels = ['Gastos', 'Ahorros']
                current_values = [savings_projection['avg_expenses'], max(0, savings_projection['avg_balance'])]
                target_values = [savings_projection['new_expense_target'], savings_projection['target_savings']]
                
                x = np.arange(len(labels))
                width = 0.35
                
                ax.bar(x - width/2, current_values, width, label='Actual', color='#FF9800')
                ax.bar(x + width/2, target_values, width, label='Objetivo', color='#4CAF50')
                
                ax.set_xticks(x)
                ax.set_xticklabels(labels)
                ax.set_ylabel('Monto (ARS)')
                ax.set_title('Distribución Actual vs. Objetivo')
                ax.legend()
                
                # Añadir etiquetas con los valores
                for i, v in enumerate(current_values):
                    ax.text(i - width/2, v + 0.5, f"${v:.0f}", ha='center')
                
                for i, v in enumerate(target_values):
                    ax.text(i + width/2, v + 0.5, f"${v:.0f}", ha='center')
                
                plt.tight_layout()
                st.pyplot(fig)
    
    # Metas Financieras (Resumen)
    goals_df = load_user_goals(username)
    if not goals_df.empty:
        st.markdown("---")
        st.subheader("🎯 Progreso de Metas Financieras")
        
        # Mostrar solo metas activas
        active_goals = goals_df[goals_df['status'] != 'Completado'].sort_values('target_date')
        
        if not active_goals.empty:
            # Mostrar las primeras 3 metas activas
            display_goals = active_goals.head(3)
            
            for _, goal in display_goals.iterrows():
                progress = calculate_goal_progress(goal)
                
                with st.container():
                    st.markdown(f"**{goal['name']}**")
                    st.progress(progress / 100)
                    st.markdown(f"${goal['current_amount']:.2f} de ${goal['target_amount']:.2f} ({progress:.1f}%)")
            
            if len(active_goals) > 3:
                st.markdown("[Ver todas las metas...](#)")
                st.markdown("*Haz clic en 'Metas Financieras' en el menú lateral para ver todas tus metas.*")
        else:
            st.info("No tienes metas financieras activas. Crea una meta en la sección 'Metas Financieras'.")
