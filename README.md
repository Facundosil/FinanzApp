# FinanzApp - Gestión Financiera Personal

Una aplicación web interactiva para gestionar finanzas personales, diseñada especialmente para usuarios hispanohablantes. Desarrollada con Streamlit y Python, ofrece una experiencia de usuario sencilla y potentes funcionalidades.

## Características Principales

- **Sistema de autenticación** de usuarios con inicio de sesión persistente
- **Gestión de transacciones**: registro de ingresos y gastos con categorización detallada
- **Sistema de cuentas múltiples**: manejo de diferentes cuentas bancarias, efectivo, etc.
- **Seguimiento de gastos en cuotas**: administración de pagos en múltiples plazos
- **Conversión automática de divisas**: USD a ARS con tasas de cambio actualizadas
  - Soporte para cotización oficial, tarjeta y blue
- **Metas financieras**: establecimiento y seguimiento de objetivos económicos
- **Reportes y estadísticas**: visualización de patrones de gastos e ingresos
- **Diseño responsivo**: interfaz adaptable con soporte para tema claro/oscuro
- **Personalización con marca**: logo y créditos personalizados

## Tecnologías Utilizadas

- **Streamlit**: Framework principal para la interfaz de usuario
- **Python**: Lenguaje de programación backend
- **Pandas**: Análisis y manipulación de datos
- **Matplotlib**: Visualización de datos y generación de gráficos
- **CSV**: Almacenamiento de datos de usuarios y transacciones

## Requisitos

- Python 3.7+
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/tu-usuario/finanzapp.git
   cd finanzapp
   ```

2. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Ejecutar la aplicación:
   ```
   streamlit run app.py
   ```

## Estructura del Proyecto

```
finanzapp/
├── app.py                     # Punto de entrada principal
├── assets/                    # Archivos estáticos (imágenes, logos)
├── data/                      # Directorio para almacenar datos de usuarios
├── pages/                     # Páginas de la aplicación
│   ├── accounts.py            # Gestión de cuentas bancarias
│   ├── dashboard.py           # Panel principal
│   ├── financial_goals.py     # Metas financieras
│   ├── profile.py             # Perfil de usuario
│   ├── reports.py             # Reportes y estadísticas
│   └── transactions.py        # Gestión de transacciones
└── utils/                     # Utilidades y funciones auxiliares
    ├── accounts.py            # Funciones para gestión de cuentas
    ├── authentication.py      # Sistema de autenticación
    ├── auto_categorize.py     # Categorización automática
    ├── currency_api.py        # API de conversión de monedas
    ├── data_handler.py        # Gestión de datos de transacciones
    ├── financial_goals.py     # Funciones para metas financieras
    ├── installment_calculator.py # Cálculo de cuotas
    └── theme_manager.py       # Gestión de temas visuales
```

## Créditos

Desarrollada por Facundo Silva de Bolso Company

## Licencia

Este proyecto está licenciado bajo términos personalizados. Consultar con el autor para más detalles.