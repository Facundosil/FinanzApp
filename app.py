import streamlit as st
import os
import pandas as pd
from datetime import datetime
import sys

# Crear directorios necesarios si no existen
for dir_path in ['data', 'data/users', '.streamlit']:
    os.makedirs(dir_path, exist_ok=True)

# Add utils directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.authentication import check_password, register_user
from utils.data_handler import load_user_data, save_transaction
from utils.currency_api import get_dollar_rate, get_dollar_rate_details
from utils.theme_manager import inicializar_tema, mostrar_selector_tema, aplicar_tema
from pages.dashboard import show_dashboard
from pages.transactions import show_transactions
from pages.profile import show_profile
from pages.reports import show_reports
from pages.financial_goals import show_financial_goals
from pages.accounts import show_accounts

# Initialize session state variables if they don't exist
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'dollar_rate' not in st.session_state:
    st.session_state.dollar_rate = None
# Para mantener la sesión activa
if 'remember_login' not in st.session_state:
    st.session_state.remember_login = False
    
# Inicializar configuración del tema
inicializar_tema()

# Crear directorio de datos si no existe
os.makedirs("data", exist_ok=True)

# Configuración de la página
st.set_page_config(
    page_title="Gestión Financiera Personal",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS adicional para mejorar la visualización en modo oscuro
st.markdown("""
<style>
/* Estilos para asegurar que todos los textos sean visibles en tema oscuro */
.dark-mode p, .dark-mode span, .dark-mode label, .dark-mode div, 
.dark-mode h1, .dark-mode h2, .dark-mode h3, .dark-mode h4, .dark-mode h5, 
.dark-mode h6, .dark-mode li, .dark-mode th, .dark-mode td {
    color: #FAFAFA !important;
}

/* Estilos para los selectores y menús desplegables */
.dark-mode div[data-baseweb="select"] span,
.dark-mode div[data-baseweb="select"] div,
.dark-mode .stSelectbox > div {
    color: #FAFAFA !important;
    border-color: #4F8BF9 !important;
}

/* Estilos para las opciones en menús desplegables */
.dark-mode div[data-baseweb="menu"] ul,
.dark-mode div[data-baseweb="menu"] li,
.dark-mode div[data-baseweb="menu"] div {
    background-color: #262730 !important;
    color: #FAFAFA !important;
}

/* Estilos para elementos de formulario */
.dark-mode .stTextInput > div > div > input,
.dark-mode .stDateInput > div > div > input {
    color: #FAFAFA !important;
    background-color: #262730 !important;
    border-color: #4F8BF9 !important;
}

/* Estilos para tablas */
.dark-mode .dataframe,
.dark-mode table {
    color: #FAFAFA !important;
}

/* Estilos para radio buttons y checkbox */
.dark-mode .stRadio label,
.dark-mode .stCheckbox label {
    color: #FAFAFA !important;
}

/* Estilos para el footer con logo y créditos */
.footer {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    margin-top: 2rem;
    padding: 1rem;
    text-align: center;
    border-top: 1px solid #ddd;
}

.footer-text {
    font-size: 1rem;
    color: #555;
    font-style: italic;
    margin-top: 0.5rem;
}

/* Ajustes para modo oscuro en el footer */
.dark-mode .footer {
    border-top: 1px solid #444;
}

.dark-mode .footer-text {
    color: #DDD !important;
}
</style>
""", unsafe_allow_html=True)

# Aplicar el tema según la selección del usuario, pero solo si está logueado
# Para la pantalla de inicio de sesión, siempre usamos el tema claro
if st.session_state.get('logged_in', False):
    # Agregar una clase para los estilos del modo oscuro si es necesario
    if st.session_state.get('theme', 'light') == 'dark':
        st.markdown('<div class="dark-mode">', unsafe_allow_html=True)
    aplicar_tema(forzar_claro=False)
else:
    # Forzar el tema claro para la pantalla de login/registro
    aplicar_tema(forzar_claro=True)

# Título de la aplicación
st.title("Gestión Financiera Personal")

# Obtener la cotización del dólar al iniciar la aplicación
try:
    if st.session_state.dollar_rate is None:
        # Obtener la cotización del dólar tarjeta
        dollar_details = get_dollar_rate_details()
        st.session_state.dollar_rate = dollar_details['rate']
        
        # Guardar detalles adicionales del dólar en la sesión para uso futuro
        st.session_state.dollar_details = dollar_details
except Exception as e:
    st.error(f"No se pudo obtener la cotización del dólar: {e}")
    st.session_state.dollar_rate = 0.0
    st.session_state.dollar_details = {
        'rate': 0.0,
        'official_rate': 0.0,
        'impuesto_pais_pct': 30.0,
        'percepcion_ganancias_pct': 30.0,
        'timestamp': datetime.now().isoformat(),
        'source': 'Error al obtener datos'
    }

# Sección de autenticación
def display_login_form():
    # CSS personalizado para el formulario de inicio de sesión
    st.markdown("""
    <style>
    .login-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-width: 600px;
        margin: 0 auto;
    }
    .stTextInput > div > div > input {
        background-color: white !important;
        color: #262730 !important;
        border: 1px solid #cccccc !important;
    }
    .stForm > div {
        background-color: white !important;
        border-radius: 5px;
        padding: 10px;
    }
    .stButton > button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor para el formulario con estilo
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        # Mostrar logo centrado
        col_logo, _, _ = st.columns([1, 0.5, 1])
        with col_logo:
            st.image("assets/bolso_company_logo.png", width=150)
        
        st.markdown('<h3 style="text-align: center;">FinanzApp</h3>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center;">Por Facundo Silva de Bolso Company</p>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            remember = st.checkbox("Mantener sesión iniciada")
            col1, col2 = st.columns(2)
            with col1:
                login_button = st.form_submit_button("Iniciar Sesión")
            with col2:
                register_button = st.form_submit_button("Registrarse")
            
            if login_button and username and password:
                if check_password(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    # Guardar preferencia para mantener la sesión
                    st.session_state.remember_login = remember
                    st.success("¡Inicio de sesión exitoso!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
            
            if register_button:
                st.session_state.show_register = True
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_register_form():
    # CSS personalizado para el formulario de registro
    st.markdown("""
    <style>
    .register-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-width: 600px;
        margin: 0 auto;
    }
    .stTextInput > div > div > input {
        background-color: white !important;
        color: #262730 !important;
        border: 1px solid #cccccc !important;
    }
    .stForm > div {
        background-color: white !important;
        border-radius: 5px;
        padding: 10px;
    }
    .stButton > button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor para el formulario con estilo
    with st.container():
        st.markdown('<div class="register-container">', unsafe_allow_html=True)
        # Mostrar logo centrado
        col_logo, _, _ = st.columns([1, 0.5, 1])
        with col_logo:
            st.image("assets/bolso_company_logo.png", width=150)
        
        st.markdown('<h3 style="text-align: center;">Registro - FinanzApp</h3>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center;">Por Facundo Silva de Bolso Company</p>', unsafe_allow_html=True)
        
        with st.form("register_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            confirm_password = st.text_input("Confirmar Contraseña", type="password")
            email = st.text_input("Correo Electrónico")
            col1, col2 = st.columns(2)
            with col1:
                register_button = st.form_submit_button("Registrarse")
            with col2:
                back_button = st.form_submit_button("Volver")
            
            if back_button:
                st.session_state.show_register = False
                st.rerun()
            
            if register_button and username and password and email:
                if password != confirm_password:
                    st.error("Las contraseñas no coinciden.")
                elif register_user(username, password, email):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    # Sesión inicia por defecto al registrarse
                    st.session_state.remember_login = True
                    st.success("Registro exitoso. ¡Bienvenido/a!")
                    st.rerun()
                else:
                    st.error("El nombre de usuario ya existe.")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Función de verificación eliminada - ya no es necesaria

# Lógica principal de la aplicación
# Si se recarga la página y el usuario eligió mantener la sesión iniciada
if st.session_state.remember_login and not st.session_state.logged_in and st.session_state.username:
    st.session_state.logged_in = True

# Si no está logueado, mostrar formularios
if not st.session_state.logged_in:
    if st.session_state.get('show_register', False):
        display_register_form()
    else:
        display_login_form()
else:
    # Sidebar navigation
    st.sidebar.title(f"¡Hola, {st.session_state.username}!")
    
    # Display current dollar rate
    st.sidebar.markdown(f"""
    💵 **Cotización Dólar**
    * **Tarjeta:** ${st.session_state.dollar_rate:.2f} ARS
    * **Oficial:** ${st.session_state.dollar_details['official_rate']:.2f} ARS
    """)
    
    # Navigation options
    nav_option = st.sidebar.radio(
        "Navegación", 
        ["Dashboard", "Transacciones", "Cuentas", "Metas Financieras", "Reportes", "Perfil"]
    )
    
    # Mostrar selector de tema
    mostrar_selector_tema()
    
    # Logout button
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.remember_login = False
        st.rerun()
    
    # Display the selected page
    if nav_option == "Dashboard":
        show_dashboard(st.session_state.username)
    elif nav_option == "Transacciones":
        show_transactions(st.session_state.username)
    elif nav_option == "Cuentas":
        show_accounts(st.session_state.username)
    elif nav_option == "Metas Financieras":
        show_financial_goals(st.session_state.username)
    elif nav_option == "Reportes":
        show_reports(st.session_state.username)
    elif nav_option == "Perfil":
        show_profile(st.session_state.username)
        
    # Añadir el footer con el logo de Bolso Company y el crédito
    st.markdown('<div class="footer">', unsafe_allow_html=True)
    st.image("assets/bolso_company_logo.png", width=120)
    st.markdown('<p class="footer-text">Creada por Facundo Silva de Bolso Company</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Cerrar el div de dark-mode si está activo
    if st.session_state.get('theme', 'light') == 'dark':
        st.markdown('</div>', unsafe_allow_html=True)
