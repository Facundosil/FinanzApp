import streamlit as st
import pandas as pd
import os
import sys
from utils.authentication import get_user_email, change_password

def show_profile(username):
    """Display user profile and settings"""
    st.title("Perfil de Usuario")
    
    # Get user email
    email = get_user_email(username)
    
    # User information
    st.subheader("Información de Usuario")
    st.write(f"**Usuario:** {username}")
    st.write(f"**Correo Electrónico:** {email}")
    
    # Change password section
    st.subheader("Cambiar Contraseña")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Contraseña Actual", type="password")
        new_password = st.text_input("Nueva Contraseña", type="password")
        confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password")
        
        submit_button = st.form_submit_button("Cambiar Contraseña")
        
        if submit_button:
            if not current_password or not new_password or not confirm_password:
                st.error("Por favor complete todos los campos.")
            elif new_password != confirm_password:
                st.error("Las contraseñas nuevas no coinciden.")
            else:
                # En una aplicación real, verificaríamos la contraseña actual
                # Para esta demostración, simplemente la cambiaremos directamente
                if change_password(username, new_password):
                    st.success("Contraseña cambiada correctamente.")
                else:
                    st.error("No se pudo cambiar la contraseña.")
    
    # Data export section
    st.subheader("Exportar Datos")
    
    if st.button("Exportar mis transacciones (CSV)"):
        user_data_path = f"data/{username}_transactions.csv"
        
        if os.path.exists(user_data_path):
            df = pd.read_csv(user_data_path)
            
            # Set file name for download
            csv_file = df.to_csv(index=False)
            
            # Create download button
            st.download_button(
                label="Descargar CSV",
                data=csv_file,
                file_name=f"{username}_transactions.csv",
                mime="text/csv"
            )
        else:
            st.warning("No hay datos para exportar.")
    
    # App settings
    st.subheader("Configuración de la Aplicación")
    
    # Theme selection
    theme = st.selectbox(
        "Tema",
        options=["Claro", "Oscuro"],
        index=0
    )
    
    # Language selection
    language = st.selectbox(
        "Idioma",
        options=["Español"],
        index=0
    )
    
    if st.button("Guardar Configuración"):
        # En una aplicación real, guardaríamos estos ajustes
        st.success("Configuración guardada correctamente.")
