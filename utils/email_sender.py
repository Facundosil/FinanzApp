import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import streamlit as st

def send_verification_email(email, verification_code):
    """
    Enviar un correo electrónico de verificación con el código de verificación
    
    En una aplicación real, esto se conectaría a un servidor SMTP y enviaría un correo electrónico.
    Para esta implementación, simularemos y mostraremos el código de verificación al usuario.
    """
    # Mostrar el código de verificación directamente en la aplicación
    st.info(f"""
    **Código de verificación simulado**
    
    Para: {email}
    Código: **{verification_code}**
    
    (En una aplicación real, este código sería enviado por correo electrónico)
    """)
    
    # Registrar en la consola también
    print(f"\n--- SIMULANDO ENVÍO DE CORREO ---")
    print(f"Para: {email}")
    print(f"Asunto: Verificación de cuenta")
    print(f"Cuerpo: Tu código de verificación es: {verification_code}")
    print(f"--- FIN DE LA SIMULACIÓN DE CORREO ---\n")
    
    # Para esta demo, asumimos que el correo se envió exitosamente
    return True

def send_password_reset_email(email, reset_code):
    """
    Enviar un correo electrónico de restablecimiento de contraseña con un código de restablecimiento
    """
    # Mostrar el código de restablecimiento directamente en la aplicación
    st.info(f"""
    **Código de recuperación de contraseña simulado**
    
    Para: {email}
    Código: **{reset_code}**
    
    (En una aplicación real, este código sería enviado por correo electrónico)
    """)
    
    # Registrar en la consola también
    print(f"\n--- SIMULANDO ENVÍO DE CORREO DE RECUPERACIÓN ---")
    print(f"Para: {email}")
    print(f"Asunto: Recuperación de contraseña")
    print(f"Cuerpo: Tu código de recuperación de contraseña es: {reset_code}")
    print(f"--- FIN DE LA SIMULACIÓN DE CORREO ---\n")
    
    # En una aplicación real, esto enviaría un correo electrónico real
    return True
