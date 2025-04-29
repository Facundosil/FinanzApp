import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

from utils.financial_goals import (
    load_user_goals, save_financial_goal, delete_financial_goal,
    get_financial_goal_by_id, update_goal_progress, calculate_goal_progress,
    get_goal_types
)
from utils.data_handler import load_user_data, get_categories

def show_financial_goals(username):
    """Muestra la página de metas financieras"""
    st.title("Metas Financieras")
    
    # Cargar las metas del usuario
    goals_df = load_user_goals(username)
    
    # Crear pestañas para cada sección
    tab1, tab2, tab3 = st.tabs(["Mis Metas", "Crear Meta", "Análisis de Metas"])
    
    with tab1:
        show_goals_list(username, goals_df)
    
    with tab2:
        show_goal_form(username)
    
    with tab3:
        show_goals_analysis(username, goals_df)

def show_goals_list(username, goals_df):
    """Muestra la lista de metas financieras del usuario"""
    st.subheader("Mis Metas Financieras")
    
    if goals_df.empty:
        st.info("No tienes metas financieras definidas. Ve a la pestaña 'Crear Meta' para comenzar.")
        return
    
    # Mostrar las metas activas primero
    active_goals = goals_df[goals_df['status'] != 'Completado'].sort_values('target_date')
    completed_goals = goals_df[goals_df['status'] == 'Completado'].sort_values('target_date', ascending=False)
    
    # Metas Activas
    if not active_goals.empty:
        st.markdown("### Metas Activas")
        for _, goal in active_goals.iterrows():
            show_goal_card(username, goal)
    
    # Metas Completadas
    if not completed_goals.empty:
        with st.expander("Metas Completadas", expanded=False):
            for _, goal in completed_goals.iterrows():
                show_goal_card(username, goal)

def show_goal_card(username, goal):
    """Muestra una tarjeta con la información de una meta financiera"""
    # Calcular el progreso
    progress = calculate_goal_progress(goal)
    
    # Crear un contenedor para la meta
    with st.container():
        # Usar columns para organizar la información
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Información básica de la meta
            st.markdown(f"**{goal['name']}**")
            st.markdown(f"*{goal['description']}*")
            st.markdown(f"Tipo: {goal['type']} | Categoría: {goal['category'] if pd.notna(goal['category']) else 'No especificada'}")
            
            # Fechas y progreso
            start_date = pd.to_datetime(goal['start_date']).strftime('%d/%m/%Y')
            target_date = pd.to_datetime(goal['target_date']).strftime('%d/%m/%Y')
            st.markdown(f"Periodo: {start_date} - {target_date}")
            
            # Barra de progreso
            st.progress(progress / 100)
            
            # Monto actual vs objetivo
            st.markdown(f"${goal['current_amount']:.2f} de ${goal['target_amount']:.2f} {goal['currency']} ({progress:.1f}%)")
        
        with col2:
            # Botones para editar, actualizar progreso y eliminar
            if st.button("✏️", key=f"edit_goal_{goal['id']}"):
                st.session_state.editing_goal = goal['id']
                st.rerun()
            
            if goal['status'] != 'Completado' and st.button("📊", key=f"update_progress_{goal['id']}"):
                st.session_state.updating_goal_progress = goal['id']
                st.rerun()
            
            if st.button("🗑️", key=f"delete_goal_{goal['id']}"):
                if delete_financial_goal(username, goal['id']):
                    st.success("Meta eliminada correctamente.")
                    st.rerun()
        
        # Si se está actualizando el progreso, mostrar el formulario
        if 'updating_goal_progress' in st.session_state and st.session_state.updating_goal_progress == goal['id']:
            with st.form(f"update_progress_form_{goal['id']}"):
                new_amount = st.number_input(
                    "Monto actual",
                    min_value=0.0,
                    value=float(goal['current_amount']),
                    step=100.0
                )
                
                submit_button = st.form_submit_button("Guardar")
                cancel_button = st.form_submit_button("Cancelar")
                
                if submit_button:
                    if update_goal_progress(username, goal['id'], new_amount):
                        st.success("Progreso actualizado correctamente.")
                        if 'updating_goal_progress' in st.session_state:
                            del st.session_state.updating_goal_progress
                        st.rerun()
                
                if cancel_button:
                    if 'updating_goal_progress' in st.session_state:
                        del st.session_state.updating_goal_progress
                    st.rerun()
        
        st.markdown("---")

def show_goal_form(username):
    """Muestra el formulario para crear o editar una meta financiera"""
    st.subheader("Crear Meta Financiera")
    
    # Valores iniciales
    goal_data = {
        'id': None,
        'name': '',
        'description': '',
        'type': 'Ahorro',
        'target_amount': 0.0,
        'current_amount': 0.0,
        'currency': 'ARS',
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'target_date': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
        'category': None,
        'status': 'En progreso',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Si estamos editando, cargar los datos de la meta
    editing = False
    if 'editing_goal' in st.session_state:
        goal_id = st.session_state.editing_goal
        existing_goal = get_financial_goal_by_id(username, goal_id)
        
        if existing_goal:
            goal_data = existing_goal
            editing = True
            st.subheader(f"Editar Meta: {goal_data['name']}")
    
    # Formulario de la meta
    with st.form("goal_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Nombre de la meta
            name = st.text_input(
                "Nombre de la Meta",
                value=goal_data['name']
            )
            
            # Descripción
            description = st.text_area(
                "Descripción",
                value=goal_data['description'],
                height=100
            )
            
            # Tipo de meta
            goal_types = get_goal_types()
            goal_type = st.selectbox(
                "Tipo de Meta",
                options=goal_types,
                index=goal_types.index(goal_data['type']) if goal_data['type'] in goal_types else 0
            )
            
            # Categoría (opcional)
            all_categories = get_categories()
            flat_categories = ["Sin categoría"] + list(all_categories.get("Ingreso", [])) + list(all_categories.get("Gasto", []))
            
            category = st.selectbox(
                "Categoría (opcional)",
                options=flat_categories,
                index=flat_categories.index(goal_data['category']) if goal_data['category'] in flat_categories else 0
            )
            
            # Corregir la categoría si se seleccionó "Sin categoría"
            if category == "Sin categoría":
                category = None
        
        with col2:
            # Monto objetivo
            target_amount = st.number_input(
                "Monto Objetivo",
                min_value=0.01,
                value=float(goal_data['target_amount']) if goal_data['target_amount'] else 1000.0,
                step=100.0
            )
            
            # Monto actual
            current_amount = st.number_input(
                "Monto Actual",
                min_value=0.0,
                value=float(goal_data['current_amount']) if goal_data['current_amount'] else 0.0,
                step=100.0
            )
            
            # Moneda
            currency = st.selectbox(
                "Moneda",
                options=["ARS", "USD"],
                index=0 if goal_data['currency'] == 'ARS' else 1
            )
            
            # Fecha de inicio
            start_date = st.date_input(
                "Fecha de Inicio",
                value=pd.to_datetime(goal_data['start_date']) if goal_data['start_date'] else datetime.now(),
                format="YYYY-MM-DD"
            )
            
            # Fecha objetivo
            target_date = st.date_input(
                "Fecha Objetivo",
                value=pd.to_datetime(goal_data['target_date']) if goal_data['target_date'] else (datetime.now() + timedelta(days=365)),
                format="YYYY-MM-DD",
                min_value=datetime.now()
            )
        
        # Botones
        submit_button = st.form_submit_button("Guardar")
        cancel_button = st.form_submit_button("Cancelar")
        
        # Procesar el formulario
        if submit_button:
            # Validaciones
            if not name:
                st.error("Debes ingresar un nombre para la meta.")
            elif target_amount <= 0:
                st.error("El monto objetivo debe ser mayor a cero.")
            elif target_date <= start_date:
                st.error("La fecha objetivo debe ser posterior a la fecha de inicio.")
            else:
                # Preparar los datos de la meta
                new_goal = {
                    'id': goal_data['id'],
                    'name': name,
                    'description': description,
                    'type': goal_type,
                    'target_amount': target_amount,
                    'current_amount': current_amount,
                    'currency': currency,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'category': category,
                    'status': 'Completado' if current_amount >= target_amount else 'En progreso',
                    'created_at': goal_data['created_at'] if 'created_at' in goal_data else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Guardar la meta
                if save_financial_goal(username, new_goal):
                    if editing:
                        st.success("Meta actualizada correctamente.")
                    else:
                        st.success("Meta creada correctamente.")
                    
                    # Limpiar el estado de edición
                    if 'editing_goal' in st.session_state:
                        del st.session_state.editing_goal
                    
                    st.rerun()
        
        if cancel_button:
            if 'editing_goal' in st.session_state:
                del st.session_state.editing_goal
            st.rerun()

def show_goals_analysis(username, goals_df):
    """Muestra análisis y gráficos de las metas financieras"""
    st.subheader("Análisis de Metas Financieras")
    
    if goals_df.empty:
        st.info("No tienes metas financieras definidas para analizar.")
        return
    
    # Crear columnas para los diferentes análisis
    col1, col2 = st.columns(2)
    
    with col1:
        # Resumen de progreso global
        st.markdown("### Progreso Global de Metas")
        
        # Calcular estadísticas
        total_goals = len(goals_df)
        completed_goals = len(goals_df[goals_df['status'] == 'Completado'])
        in_progress_goals = total_goals - completed_goals
        progress_percentage = (completed_goals / total_goals) * 100 if total_goals > 0 else 0
        
        # Mostrar estadísticas
        st.markdown(f"**Total de metas:** {total_goals}")
        st.markdown(f"**Metas completadas:** {completed_goals}")
        st.markdown(f"**Metas en progreso:** {in_progress_goals}")
        
        # Gráfico de progreso global
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(
            [completed_goals, in_progress_goals],
            labels=['Completadas', 'En progreso'],
            autopct='%1.1f%%',
            startangle=90,
            colors=['#4CAF50', '#2196F3']
        )
        ax.axis('equal')
        st.pyplot(fig)
    
    with col2:
        # Gráfico por tipo de meta
        st.markdown("### Metas por Tipo")
        
        # Contar por tipo
        goal_types_count = goals_df['type'].value_counts()
        
        # Gráfico de barras horizontal
        fig, ax = plt.subplots(figsize=(5, 4))
        goal_types_count.plot(kind='barh', ax=ax, color='#673AB7')
        ax.set_xlabel('Cantidad')
        ax.set_ylabel('Tipo de Meta')
        st.pyplot(fig)
    
    # Progreso individual de metas activas
    st.markdown("### Progreso de Metas Activas")
    
    # Filtrar sólo las metas activas
    active_goals = goals_df[goals_df['status'] != 'Completado']
    
    if active_goals.empty:
        st.info("No tienes metas activas para mostrar.")
        return
    
    # Calcular progreso para cada meta
    progress_data = []
    for _, goal in active_goals.iterrows():
        progress = calculate_goal_progress(goal)
        progress_data.append({
            'name': goal['name'],
            'progress': progress,
            'remaining': 100 - progress
        })
    
    # Convertir a DataFrame para facilitar la creación del gráfico
    progress_df = pd.DataFrame(progress_data)
    
    # Gráfico de barras apiladas horizontal
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Ordenar por progreso para mejor visualización
    progress_df = progress_df.sort_values('progress')
    
    # Crear gráfico
    ax.barh(progress_df['name'], progress_df['progress'], color='#4CAF50', label='Progreso')
    ax.barh(progress_df['name'], progress_df['remaining'], left=progress_df['progress'], color='#E0E0E0', label='Restante')
    
    # Agregar porcentajes
    for i, (_, row) in enumerate(progress_df.iterrows()):
        ax.text(row['progress'] + 2, i, f"{row['progress']:.1f}%", va='center')
    
    ax.set_xlabel('Porcentaje de Progreso')
    ax.set_xlim(0, 100)
    ax.legend(loc='lower right')
    
    st.pyplot(fig)
    
    # Mostrar próximas fechas límite
    st.markdown("### Próximas Fechas Límite")
    
    # Ordenar por fecha objetivo
    upcoming_goals = active_goals.sort_values('target_date')
    
    # Mostrar en formato de tabla
    upcoming_df = upcoming_goals[['name', 'target_date', 'target_amount', 'current_amount', 'currency']]
    upcoming_df = upcoming_df.rename(columns={
        'name': 'Meta',
        'target_date': 'Fecha Límite',
        'target_amount': 'Monto Objetivo',
        'current_amount': 'Monto Actual',
        'currency': 'Moneda'
    })
    
    # Formatear la fecha
    upcoming_df['Fecha Límite'] = pd.to_datetime(upcoming_df['Fecha Límite']).dt.strftime('%d/%m/%Y')
    
    # Mostrar la tabla
    st.dataframe(upcoming_df)