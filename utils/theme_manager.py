import streamlit as st

def inicializar_tema():
    """
    Inicializa la configuración del tema.
    Configura una variable de sesión para controlar el tema actual.
    """
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'

def cambiar_tema(tema):
    """
    Cambia entre el tema claro y oscuro.
    
    Args:
        tema: 'light' o 'dark'
    """
    # Guardar el tema actual en la sesión
    st.session_state.theme = tema
    return True

def obtener_tema_actual():
    """
    Obtiene el tema actual
    
    Returns:
        'light' o 'dark'
    """
    return st.session_state.get('theme', 'light')

def aplicar_tema(forzar_claro=False):
    """
    Aplica el CSS del tema seleccionado.
    
    Args:
        forzar_claro: Si es True, aplica siempre el tema claro, ignorando la preferencia del usuario
    """
    tema_actual = 'light' if forzar_claro else obtener_tema_actual()
    
    # Estilos base compartidos por todos los temas
    base_css = """
    <style>
    #MainMenu {visibility: hidden;}
    .stApp > header {display: none;}
    .css-1adrfps {padding-top: 1rem;}
    /* La flecha para colapsar la sidebar ahora se muestra */
    /* [data-testid="collapsedControl"] {display: none} */
    ul[data-testid="main-menu-list"] {display: none;}
    div[data-testid="stSidebarNav"] {display: none;}
    </style>
    """
    
    # Estilos específicos del tema claro
    light_css = """
    <style>
    .stApp {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    .stSidebar {
        background-color: #F0F2F6 !important;
    }
    /* Estilo para el botón de colapso en modo claro */
    [data-testid="collapsedControl"] {
        color: #262730 !important;
        font-size: 20px !important;
        font-weight: bold !important;
    }
    [data-testid="collapsedControl"] svg path {
        fill: #262730 !important;
        stroke: #262730 !important;
    }
    .stButton>button {
        background-color: #1E88E5 !important;
        color: white !important;
    }
    .stButton>button:hover {
        background-color: #4B9BE6 !important;
    }
    .stTextInput>div>div>input, .stSelectbox, .stDateInput>div>div>input {
        background-color: white !important;
        color: #262730 !important;
    }
    .stCheckbox>div>div>p {
        color: #262730 !important;
    }
    .stForm {
        background-color: #FFFFFF !important;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """
    
    # Estilos específicos del tema oscuro
    dark_css = """
    <style>
    .stApp {
        background-color: #0E1117 !important;
        color: #FAFAFA !important;
    }
    .stSidebar {
        background-color: #262730 !important;
    }
    /* Hacer el botón de colapso blanco en modo oscuro */
    [data-testid="collapsedControl"] {
        color: white !important;
        font-size: 20px !important;
        font-weight: bold !important;
    }
    [data-testid="collapsedControl"] svg path {
        fill: white !important;
        stroke: white !important;
    }
    .stButton>button {
        background-color: #4F8BF9 !important;
        color: white !important;
    }
    .stButton>button:hover {
        background-color: #6D9EF3 !important;
    }
    .stTextInput>div>div>input, .stSelectbox, .stDateInput>div>div>input {
        background-color: #262730 !important;
        color: #FAFAFA !important;
        border-color: #4F8BF9 !important;
    }
    /* Asegurar que los textos por defecto sean legibles en modo oscuro */
    p, span, label, h1, h2, h3, h4, h5, h6, li {
        color: #FAFAFA !important;
    }
    .stCheckbox>div>div>p {
        color: #FAFAFA !important;
    }
    /* Estilos para selectores y menús desplegables */
    .stSelectbox>div>div>div>div>div {
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }
    /* Estilos para las opciones en selectores */
    div[data-baseweb="select"] span {
        color: #FAFAFA !important;
    }
    /* Estilos para los elementos de formulario */
    .stForm {
        background-color: #262730 !important;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    /* Asegurar que los textos en tablas y dataframes sean visibles */
    .dataframe {
        color: #FAFAFA !important;
    }
    .dataframe th, .dataframe td {
        color: #FAFAFA !important;
    }
    /* Estilos específicos para mejorar la visualización de tablas en modo oscuro */
    table {
        color: #FAFAFA !important;
    }
    th, td {
        color: #FAFAFA !important;
    }
    /* Cambia el color de texto para todos los elementos dentro de tablas de datos */
    [data-testid="stTable"] {
        color: #FFFFFF !important;
    }
    [data-testid="stTable"] div {
        color: #FFFFFF !important;
    }
    /* Estilos específicos para los dataframes de Streamlit */
    [data-testid="stDataFrame"] div {
        color: #FFFFFF !important;
    }
    [data-testid="stDataFrame"] th div p {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    [data-testid="stDataFrame"] td div p {
        color: #FFFFFF !important;
    }
    /* Estilos para radio buttons y checkbox */
    .stRadio label, .stCheckbox label {
        color: #FAFAFA !important;
    }
    </style>
    """
    
    # Aplicar los estilos según el tema
    st.markdown(base_css, unsafe_allow_html=True)
    
    if tema_actual == 'dark':
        st.markdown(dark_css, unsafe_allow_html=True)
    else:
        st.markdown(light_css, unsafe_allow_html=True)

def mostrar_selector_tema():
    """
    Muestra un selector de tema en la barra lateral
    """
    tema_actual = obtener_tema_actual()
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Personalización")
        
        # Título para el selector de tema
        st.markdown("**Tema de la aplicación:**")
        
        # Creamos una fila para los botones
        col1, col2 = st.columns(2)
        
        with col1:
            # Botón para el tema claro
            if st.button("☀️ Claro", disabled=tema_actual == 'light'):
                cambiar_tema('light')
                st.rerun()
                
        with col2:
            # Botón para el tema oscuro
            if st.button("🌙 Oscuro", disabled=tema_actual == 'dark'):
                cambiar_tema('dark')
                st.rerun()