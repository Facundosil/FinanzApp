import requests
import json
import os
import pandas as pd
from datetime import datetime, timedelta

# Almacenar en caché la cotización del dólar por 1 hora para evitar llamadas excesivas a la API
CACHE_FILE = "data/dollar_rate_cache.json"
HISTORICAL_CACHE_FILE = "data/dollar_rate_historical_cache.json"

def get_dollar_rate():
    """
    Obtener la cotización actual del dólar desde una API
    Devuelve la cotización del dólar tarjeta (cotización oficial + impuestos) para Argentina
    """
    try:
        # Verificar si tenemos una cotización en caché reciente
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as file:
                cache_data = json.load(file)
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                
                # Si la caché tiene menos de 1 hora, usarla
                if datetime.now() - cache_time < timedelta(hours=1):
                    return cache_data['rate']
        
        # No hay caché reciente, obtener de la API del BCRA a través de bluelytics
        # (bluelytics proporciona una API más estable y actualizada que consulta fuentes oficiales)
        response = requests.get("https://api.bluelytics.com.ar/v2/latest")
        response.raise_for_status()
        
        data = response.json()
        
        # Obtener la cotización oficial del dólar
        official_rate = data['oficial']['value_sell']
        
        # Obtener la cotización del dólar blue
        blue_rate = data['blue']['value_sell']
        
        # Impuestos actuales para el dólar tarjeta en Argentina (PAIS 30% + RG 5463 30%)
        impuesto_pais = 0.30
        percepcion_ganancias = 0.30
        
        # Calcular el dólar tarjeta (oficial + impuestos)
        card_rate = official_rate * (1 + impuesto_pais + percepcion_ganancias)
        
        # Guardar el resultado en caché
        cache_data = {
            'rate': card_rate,
            'official_rate': official_rate,
            'blue_rate': blue_rate,
            'impuesto_pais_pct': impuesto_pais * 100,
            'percepcion_ganancias_pct': percepcion_ganancias * 100,
            'timestamp': datetime.now().isoformat(),
            'source': 'Bluelytics (fuente oficial)'
        }
        
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w') as file:
            json.dump(cache_data, file)
        
        # Actualizar histórico
        update_historical_rate(official_rate, card_rate, blue_rate)
        
        return card_rate
    
    except Exception as e:
        print(f"Error al obtener la cotización del dólar: {e}")
        
        # Si tenemos algún valor en caché, devolverlo aunque sea antiguo
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as file:
                    return json.load(file)['rate']
            except:
                pass
        
        # Valor de respaldo
        return 1000.0  # Valor aproximado de respaldo para ARS/USD

def get_dollar_rate_details():
    """
    Obtener detalles completos de la cotización del dólar, incluyendo oficial, tarjeta y blue
    """
    try:
        # Intentar refrescar los datos
        get_dollar_rate()
        
        # Leer los datos de la caché
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as file:
                return json.load(file)
        
        # Si no hay caché, crear datos predeterminados
        return {
            'rate': 1000.0,
            'official_rate': 900.0,
            'blue_rate': 1100.0,
            'impuesto_pais_pct': 30.0,
            'percepcion_ganancias_pct': 30.0,
            'timestamp': datetime.now().isoformat(),
            'source': 'Valor predeterminado (sin conexión)'
        }
    except Exception as e:
        print(f"Error al obtener detalles de la cotización: {e}")
        return {
            'rate': 1000.0,
            'official_rate': 900.0,
            'blue_rate': 1100.0,
            'impuesto_pais_pct': 30.0,
            'percepcion_ganancias_pct': 30.0,
            'timestamp': datetime.now().isoformat(),
            'source': 'Valor predeterminado (error)'
        }

def update_historical_rate(official_rate, card_rate, blue_rate=None):
    """
    Actualizar el registro histórico de cotizaciones del dólar
    
    Args:
        official_rate: Cotización oficial
        card_rate: Cotización tarjeta
        blue_rate: Cotización blue (opcional)
    """
    try:
        today = datetime.now().date().isoformat()
        historical_data = {}
        
        # Cargar datos históricos existentes
        if os.path.exists(HISTORICAL_CACHE_FILE):
            with open(HISTORICAL_CACHE_FILE, 'r') as file:
                historical_data = json.load(file)
        
        # Actualizar con la cotización de hoy
        rate_data = {
            'official_rate': official_rate,
            'card_rate': card_rate
        }
        
        # Añadir cotización blue si está disponible
        if blue_rate is not None:
            rate_data['blue_rate'] = blue_rate
            
        historical_data[today] = rate_data
        
        # Guardar el histórico actualizado
        os.makedirs(os.path.dirname(HISTORICAL_CACHE_FILE), exist_ok=True)
        with open(HISTORICAL_CACHE_FILE, 'w') as file:
            json.dump(historical_data, file)
            
    except Exception as e:
        print(f"Error al actualizar histórico de cotizaciones: {e}")

def get_historical_rates(days=30):
    """
    Obtener el histórico de cotizaciones del dólar de los últimos días
    
    Args:
        days: Número de días para mostrar
    
    Returns:
        DataFrame con las cotizaciones históricas
    """
    try:
        # Verificar si tenemos datos históricos
        if not os.path.exists(HISTORICAL_CACHE_FILE):
            # Si no hay histórico, crear uno con el valor actual
            get_dollar_rate()
        
        # Cargar datos históricos
        with open(HISTORICAL_CACHE_FILE, 'r') as file:
            historical_data = json.load(file)
        
        # Convertir a DataFrame
        data = []
        for date_str, rates in historical_data.items():
            entry = {
                'date': date_str,
                'official_rate': rates['official_rate'],
                'card_rate': rates['card_rate']
            }
            
            # Añadir blue_rate si está disponible
            if 'blue_rate' in rates:
                entry['blue_rate'] = rates['blue_rate']
            
            data.append(entry)
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Si no hay columna de dólar blue, crearla con valores nulos
        if 'blue_rate' not in df.columns:
            df['blue_rate'] = None
        
        # Limitar a los últimos N días
        if len(df) > days:
            df = df.tail(days)
        
        return df
    
    except Exception as e:
        print(f"Error al obtener histórico de cotizaciones: {e}")
        # Crear un DataFrame vacío
        return pd.DataFrame(columns=['date', 'official_rate', 'card_rate', 'blue_rate'])
