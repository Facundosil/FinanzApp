import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import calendar
import sys
import os
from utils.data_handler import load_user_data

def show_reports(username):
    """Display financial reports and analysis"""
    st.title("Reportes y Análisis")
    
    # Load user data
    df = load_user_data(username)
    
    if df.empty:
        st.info("No hay datos de transacciones para generar reportes.")
        return
    
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Report type selection
    report_type = st.selectbox(
        "Tipo de Reporte",
        options=[
            "Balance Mensual",
            "Gastos por Categoría",
            "Evolución de Ingresos y Gastos",
            "Gastos Fijos vs Variables",
            "Análisis de Monedas"
        ]
    )
    
    # Filter by year
    years = sorted(df['date'].dt.year.unique(), reverse=True)
    selected_year = st.selectbox("Año", options=years)
    
    # Filter data by selected year
    yearly_data = df[df['date'].dt.year == selected_year]
    
    # Show the selected report
    if report_type == "Balance Mensual":
        show_monthly_balance(yearly_data, selected_year)
    elif report_type == "Gastos por Categoría":
        show_expenses_by_category(yearly_data, selected_year)
    elif report_type == "Evolución de Ingresos y Gastos":
        show_income_expense_evolution(yearly_data, selected_year)
    elif report_type == "Gastos Fijos vs Variables":
        show_fixed_vs_variable_expenses(yearly_data, selected_year)
    elif report_type == "Análisis de Monedas":
        show_currency_analysis(yearly_data, selected_year)

def show_monthly_balance(df, year):
    """Show monthly balance report"""
    st.subheader(f"Balance Mensual {year}")
    
    # Group by month and calculate totals
    monthly_data = df.groupby(df['date'].dt.month).agg({
        'amount_pesos': lambda x: 0  # Placeholder
    }).reset_index()
    
    # Add month names
    monthly_data['month_name'] = monthly_data['date'].apply(lambda x: calendar.month_name[x])
    
    # Calculate income, expenses and balance for each month
    monthly_incomes = []
    monthly_expenses = []
    monthly_balances = []
    
    for month in range(1, 13):
        month_df = df[df['date'].dt.month == month]
        
        income = month_df[month_df['type'] == 'Ingreso']['amount_pesos'].sum()
        expense = month_df[month_df['type'] == 'Gasto']['amount_pesos'].sum()
        balance = income - expense
        
        monthly_incomes.append(income)
        monthly_expenses.append(expense)
        monthly_balances.append(balance)
    
    # Create a DataFrame for the report
    months = [calendar.month_name[i] for i in range(1, 13)]
    report_df = pd.DataFrame({
        'Mes': months,
        'Ingresos': monthly_incomes,
        'Gastos': monthly_expenses,
        'Balance': monthly_balances
    })
    
    # Display as a table
    st.dataframe(
        report_df,
        column_config={
            'Mes': st.column_config.TextColumn("Mes"),
            'Ingresos': st.column_config.NumberColumn("Ingresos", format="$%.2f"),
            'Gastos': st.column_config.NumberColumn("Gastos", format="$%.2f"),
            'Balance': st.column_config.NumberColumn("Balance", format="$%.2f")
        },
        hide_index=True
    )
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(months))
    width = 0.25
    
    # Plot bars
    ax.bar(x - width, monthly_incomes, width, label='Ingresos', color='green')
    ax.bar(x, monthly_expenses, width, label='Gastos', color='red')
    ax.bar(x + width, monthly_balances, width, label='Balance', color='blue')
    
    # Add labels and legend
    ax.set_ylabel('Monto (ARS)')
    ax.set_title(f'Balance Mensual {year}')
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45)
    ax.legend()
    
    # Add grid for better readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Show plot
    plt.tight_layout()
    st.pyplot(fig)

def show_expenses_by_category(df, year):
    """Show expenses by category report"""
    st.subheader(f"Gastos por Categoría {year}")
    
    # Filter only expenses
    expenses_df = df[df['type'] == 'Gasto']
    
    if expenses_df.empty:
        st.info(f"No hay gastos registrados para el año {year}.")
        return
    
    # Group by category
    category_expenses = expenses_df.groupby('category')['amount_pesos'].sum().sort_values(ascending=False)
    
    # Display as a table
    category_df = pd.DataFrame({
        'Categoría': category_expenses.index,
        'Monto': category_expenses.values,
        'Porcentaje': (category_expenses.values / category_expenses.sum() * 100)
    })
    
    st.dataframe(
        category_df,
        column_config={
            'Categoría': st.column_config.TextColumn("Categoría"),
            'Monto': st.column_config.NumberColumn("Monto", format="$%.2f"),
            'Porcentaje': st.column_config.NumberColumn("Porcentaje", format="%.1f%%")
        },
        hide_index=True
    )
    
    # Pie chart
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # If there are too many categories, show only top 8 and group the rest
    if len(category_expenses) > 8:
        top_categories = category_expenses.iloc[:7]
        others = pd.Series({'Otros': category_expenses.iloc[7:].sum()})
        plot_data = pd.concat([top_categories, others])
    else:
        plot_data = category_expenses
    
    plot_data.plot(kind='pie', autopct='%1.1f%%', ax=ax, startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title(f'Distribución de Gastos por Categoría {year}')
    
    # Show plot
    plt.tight_layout()
    st.pyplot(fig)
    
    # Monthly breakdown by category
    st.subheader("Desglose Mensual por Categoría")
    
    # Group by month and category
    monthly_category = expenses_df.groupby([expenses_df['date'].dt.month, 'category'])['amount_pesos'].sum().unstack().fillna(0)
    
    # Add month names
    monthly_category.index = [calendar.month_name[m] for m in monthly_category.index]
    
    # Create a stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    monthly_category.plot(kind='bar', stacked=True, ax=ax)
    
    # Add labels
    ax.set_ylabel('Monto (ARS)')
    ax.set_title(f'Gastos Mensuales por Categoría {year}')
    plt.xticks(rotation=45)
    
    # Add grid for better readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Show plot
    plt.tight_layout()
    st.pyplot(fig)

def show_income_expense_evolution(df, year):
    """Show income vs expense evolution"""
    st.subheader(f"Evolución de Ingresos y Gastos {year}")
    
    # Group by month and type
    monthly_evolution = df.groupby([df['date'].dt.month, 'type'])['amount_pesos'].sum().unstack().fillna(0)
    
    # Add month names
    monthly_evolution.index = [calendar.month_name[m] for m in monthly_evolution.index]
    
    # Ensure both columns exist
    if 'Ingreso' not in monthly_evolution.columns:
        monthly_evolution['Ingreso'] = 0
    if 'Gasto' not in monthly_evolution.columns:
        monthly_evolution['Gasto'] = 0
    
    # Calculate savings rate
    monthly_evolution['Tasa de Ahorro (%)'] = (
        (monthly_evolution['Ingreso'] - monthly_evolution['Gasto']) / 
        monthly_evolution['Ingreso'] * 100
    ).fillna(0)
    
    # Display as a table
    st.dataframe(
        monthly_evolution,
        column_config={
            'Ingreso': st.column_config.NumberColumn("Ingresos", format="$%.2f"),
            'Gasto': st.column_config.NumberColumn("Gastos", format="$%.2f"),
            'Tasa de Ahorro (%)': st.column_config.NumberColumn("Tasa de Ahorro", format="%.1f%%")
        }
    )
    
    # Plot the evolution
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot income and expenses
    monthly_evolution['Ingreso'].plot(kind='line', marker='o', color='green', ax=ax1, label='Ingresos')
    monthly_evolution['Gasto'].plot(kind='line', marker='x', color='red', ax=ax1, label='Gastos')
    
    # Create a secondary y-axis for savings rate
    ax2 = ax1.twinx()
    monthly_evolution['Tasa de Ahorro (%)'].plot(kind='bar', alpha=0.3, color='blue', ax=ax2, label='Tasa de Ahorro')
    
    # Add labels and legend
    ax1.set_ylabel('Monto (ARS)')
    ax2.set_ylabel('Tasa de Ahorro (%)')
    ax1.set_title(f'Evolución de Ingresos, Gastos y Tasa de Ahorro {year}')
    
    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')
    
    # Add grid for better readability
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Show plot
    plt.tight_layout()
    st.pyplot(fig)
    
    # Cumulative view
    st.subheader("Vista Acumulada")
    
    # Calculate cumulative values
    cumulative = monthly_evolution[['Ingreso', 'Gasto']].cumsum()
    cumulative['Balance'] = cumulative['Ingreso'] - cumulative['Gasto']
    
    # Display as a table
    st.dataframe(
        cumulative,
        column_config={
            'Ingreso': st.column_config.NumberColumn("Ingresos Acumulados", format="$%.2f"),
            'Gasto': st.column_config.NumberColumn("Gastos Acumulados", format="$%.2f"),
            'Balance': st.column_config.NumberColumn("Balance Acumulado", format="$%.2f")
        }
    )
    
    # Plot cumulative values
    fig, ax = plt.subplots(figsize=(12, 6))
    
    cumulative.plot(kind='line', marker='o', ax=ax)
    
    # Add labels
    ax.set_ylabel('Monto Acumulado (ARS)')
    ax.set_title(f'Valores Acumulados {year}')
    
    # Add grid for better readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Show plot
    plt.tight_layout()
    st.pyplot(fig)

def show_fixed_vs_variable_expenses(df, year):
    """Show fixed vs variable expenses analysis"""
    st.subheader(f"Gastos Fijos vs Variables {year}")
    
    # Filter only expenses
    expenses_df = df[df['type'] == 'Gasto']
    
    if expenses_df.empty:
        st.info(f"No hay gastos registrados para el año {year}.")
        return
    
    # Group by fixed expense flag
    fixed_variable = expenses_df.groupby('fixed_expense')['amount_pesos'].sum()
    
    # Make sure both categories exist
    if True not in fixed_variable.index:
        fixed_variable[True] = 0
    if False not in fixed_variable.index:
        fixed_variable[False] = 0
    
    # Calculate percentages
    total_expenses = fixed_variable.sum()
    fixed_percent = (fixed_variable[True] / total_expenses * 100) if total_expenses > 0 else 0
    variable_percent = (fixed_variable[False] / total_expenses * 100) if total_expenses > 0 else 0
    
    # Display totals
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Gastos Totales", f"${total_expenses:.2f}")
    
    with col2:
        st.metric("Gastos Fijos", f"${fixed_variable[True]:.2f} ({fixed_percent:.1f}%)")
    
    with col3:
        st.metric("Gastos Variables", f"${fixed_variable[False]:.2f} ({variable_percent:.1f}%)")
    
    # Pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    
    fixed_variable.index = ['Fijos', 'Variables']
    fixed_variable.plot(kind='pie', autopct='%1.1f%%', ax=ax, startangle=90, colors=['#ff9999', '#66b3ff'])
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title('Distribución de Gastos Fijos vs Variables')
    
    # Show plot
    plt.tight_layout()
    st.pyplot(fig)
    
    # Monthly breakdown
    st.subheader("Desglose Mensual")
    
    # Group by month and fixed_expense
    monthly_fixed_var = expenses_df.groupby([expenses_df['date'].dt.month, 'fixed_expense'])['amount_pesos'].sum().unstack().fillna(0)
    
    # Rename columns
    monthly_fixed_var.columns = ['Fijos', 'Variables'] if False in monthly_fixed_var.columns else ['Variables', 'Fijos']
    
    # Add month names
    monthly_fixed_var.index = [calendar.month_name[m] for m in monthly_fixed_var.index]
    
    # Display as a table
    st.dataframe(
        monthly_fixed_var,
        column_config={
            'Fijos': st.column_config.NumberColumn("Gastos Fijos", format="$%.2f"),
            'Variables': st.column_config.NumberColumn("Gastos Variables", format="$%.2f")
        }
    )
    
    # Stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 6))
    
    monthly_fixed_var.plot(kind='bar', stacked=True, ax=ax, color=['#ff9999', '#66b3ff'])
    
    # Add labels
    ax.set_ylabel('Monto (ARS)')
    ax.set_title('Gastos Fijos vs Variables por Mes')
    plt.xticks(rotation=45)
    
    # Add grid for better readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Show plot
    plt.tight_layout()
    st.pyplot(fig)

def show_currency_analysis(df, year):
    """Show currency analysis"""
    st.subheader(f"Análisis de Monedas {year}")
    
    # Group by currency
    currency_totals = df.groupby(['type', 'currency'])['amount_pesos'].sum().unstack().fillna(0)
    
    # Make sure both currencies exist
    if 'ARS' not in currency_totals.columns:
        currency_totals['ARS'] = 0
    if 'USD' not in currency_totals.columns:
        currency_totals['USD'] = 0
    
    # Original amounts (before conversion)
    original_amounts = df.groupby(['type', 'currency'])['amount'].sum().unstack().fillna(0)
    
    # Combine into a display table
    currency_table = pd.DataFrame({
        'Pesos (ARS)': currency_totals['ARS'],
        'Dólares (USD)': original_amounts.get('USD', pd.Series([0, 0], index=['Ingreso', 'Gasto'])),
        'Equivalente en Pesos': currency_totals['USD']
    })
    
    # Display as a table
    st.dataframe(
        currency_table,
        column_config={
            'Pesos (ARS)': st.column_config.NumberColumn("Pesos (ARS)", format="$%.2f"),
            'Dólares (USD)': st.column_config.NumberColumn("Dólares (USD)", format="$%.2f"),
            'Equivalente en Pesos': st.column_config.NumberColumn("Dólares en Pesos", format="$%.2f")
        }
    )
    
    # Pie charts for distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribución de Ingresos por Moneda")
        
        # Income distribution
        if 'Ingreso' in currency_totals.index:
            income_currency = pd.Series({
                'ARS': currency_totals.loc['Ingreso', 'ARS'],
                'USD': currency_totals.loc['Ingreso', 'USD']
            })
            
            # Pie chart
            fig, ax = plt.subplots(figsize=(6, 6))
            income_currency.plot(kind='pie', autopct='%1.1f%%', ax=ax, startangle=90, colors=['#66b3ff', '#99ff99'])
            plt.axis('equal')
            plt.title('Ingresos por Moneda')
            
            # Show plot
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("No hay ingresos registrados.")
    
    with col2:
        st.subheader("Distribución de Gastos por Moneda")
        
        # Expense distribution
        if 'Gasto' in currency_totals.index:
            expense_currency = pd.Series({
                'ARS': currency_totals.loc['Gasto', 'ARS'],
                'USD': currency_totals.loc['Gasto', 'USD']
            })
            
            # Pie chart
            fig, ax = plt.subplots(figsize=(6, 6))
            expense_currency.plot(kind='pie', autopct='%1.1f%%', ax=ax, startangle=90, colors=['#ff9999', '#ffcc99'])
            plt.axis('equal')
            plt.title('Gastos por Moneda')
            
            # Show plot
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("No hay gastos registrados.")
    
    # Monthly breakdown by currency
    st.subheader("Gastos Mensuales por Moneda")
    
    # Filter only expenses
    expenses_df = df[df['type'] == 'Gasto']
    
    if not expenses_df.empty:
        # Group by month and currency
        monthly_currency = expenses_df.groupby([expenses_df['date'].dt.month, 'currency'])['amount_pesos'].sum().unstack().fillna(0)
        
        # Make sure both currencies exist
        if 'ARS' not in monthly_currency.columns:
            monthly_currency['ARS'] = 0
        if 'USD' not in monthly_currency.columns:
            monthly_currency['USD'] = 0
        
        # Add month names
        monthly_currency.index = [calendar.month_name[m] for m in monthly_currency.index]
        
        # Display as a table
        st.dataframe(
            monthly_currency,
            column_config={
                'ARS': st.column_config.NumberColumn("Pesos (ARS)", format="$%.2f"),
                'USD': st.column_config.NumberColumn("Dólares en Pesos", format="$%.2f")
            }
        )
        
        # Bar chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        monthly_currency.plot(kind='bar', ax=ax, color=['#66b3ff', '#99ff99'])
        
        # Add labels
        ax.set_ylabel('Monto (ARS)')
        ax.set_title('Gastos Mensuales por Moneda')
        plt.xticks(rotation=45)
        
        # Add grid for better readability
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Show plot
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No hay gastos registrados para mostrar el desglose mensual por moneda.")
