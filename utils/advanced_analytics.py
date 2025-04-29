import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar

def get_spending_forecast(df, months_ahead=3):
    """
    Forecast spending for the next few months based on historical data.
    
    Args:
        df: DataFrame containing transaction data
        months_ahead: Number of months to forecast
        
    Returns:
        DataFrame with forecasted expenses by category
    """
    if df.empty:
        return pd.DataFrame()
    
    # Filter to only include expenses
    expenses_df = df[df['type'] == 'Gasto'].copy()
    
    if expenses_df.empty:
        return pd.DataFrame()
    
    # Convert date to datetime if not already
    expenses_df['date'] = pd.to_datetime(expenses_df['date'])
    
    # Group by month and category
    expenses_df['month'] = expenses_df['date'].dt.strftime('%Y-%m')
    monthly_by_category = expenses_df.groupby(['month', 'category'])['amount_pesos'].sum().reset_index()
    
    # Get unique categories
    categories = expenses_df['category'].unique()
    
    # Get the last few months of data
    unique_months = sorted(monthly_by_category['month'].unique())
    
    if len(unique_months) < 3:
        # Not enough data for reliable forecast
        return pd.DataFrame()
    
    # Use the last 3-6 months for forecasting if available
    num_months_for_forecast = min(6, len(unique_months))
    recent_months = unique_months[-num_months_for_forecast:]
    
    # Calculate average monthly spending by category
    recent_data = monthly_by_category[monthly_by_category['month'].isin(recent_months)]
    avg_by_category = recent_data.groupby('category')['amount_pesos'].mean().reset_index()
    
    # For each category, calculate variance to determine trend
    trend_by_category = {}
    for category in categories:
        cat_data = recent_data[recent_data['category'] == category]
        if len(cat_data) > 1:
            # Simple linear regression to detect trend
            x = np.arange(len(cat_data))
            y = cat_data['amount_pesos'].values
            if len(x) > 0 and len(y) > 0:
                z = np.polyfit(x, y, 1)
                trend_by_category[category] = z[0]  # Slope indicates trend direction
            else:
                trend_by_category[category] = 0
        else:
            trend_by_category[category] = 0
    
    # Create forecast for the next few months
    forecast_data = []
    current_month = datetime.now()
    
    for i in range(1, months_ahead + 1):
        forecast_month = current_month + pd.DateOffset(months=i)
        forecast_month_str = forecast_month.strftime('%Y-%m')
        
        for _, row in avg_by_category.iterrows():
            category = row['category']
            base_amount = row['amount_pesos']
            
            # Apply trend factor (with dampening for longer forecasts)
            trend_factor = 1 + (trend_by_category.get(category, 0) * (0.8 ** i))
            forecast_amount = base_amount * trend_factor
            
            forecast_data.append({
                'month': forecast_month_str,
                'category': category,
                'amount_pesos': forecast_amount,
                'forecast': True
            })
    
    # Create DataFrame
    forecast_df = pd.DataFrame(forecast_data)
    return forecast_df

def detect_unusual_spending(df, threshold_factor=1.5):
    """
    Detect unusual spending patterns based on historical averages.
    
    Args:
        df: DataFrame containing transaction data
        threshold_factor: Factor above average to consider as unusual
        
    Returns:
        DataFrame with detected unusual transactions
    """
    if df.empty:
        return pd.DataFrame()
    
    # Filter to only include expenses
    expenses_df = df[df['type'] == 'Gasto'].copy()
    
    if expenses_df.empty:
        return pd.DataFrame()
    
    # Convert date to datetime if not already
    expenses_df['date'] = pd.to_datetime(expenses_df['date'])
    
    # Get the current month
    today = datetime.now()
    current_month_start = datetime(today.year, today.month, 1)
    
    # Calculate average monthly spending by category (excluding current month)
    expenses_df['month'] = expenses_df['date'].dt.strftime('%Y-%m')
    historical_df = expenses_df[expenses_df['date'] < current_month_start]
    
    if historical_df.empty:
        return pd.DataFrame()  # Not enough data
    
    # Group by category and calculate average
    avg_by_category = historical_df.groupby('category')['amount_pesos'].mean().reset_index()
    avg_by_category = avg_by_category.rename(columns={'amount_pesos': 'avg_amount'})
    
    # Get current month spending
    current_month_df = expenses_df[expenses_df['date'] >= current_month_start]
    
    if current_month_df.empty:
        return pd.DataFrame()  # No current month data
    
    current_spending = current_month_df.groupby('category')['amount_pesos'].sum().reset_index()
    current_spending = current_spending.rename(columns={'amount_pesos': 'current_amount'})
    
    # Merge average and current spending
    comparison = pd.merge(current_spending, avg_by_category, on='category', how='left')
    
    # Filter to categories with unusual spending
    unusual = comparison[comparison['current_amount'] > comparison['avg_amount'] * threshold_factor]
    
    # Add percentage increase
    if not unusual.empty:
        unusual['percent_increase'] = ((unusual['current_amount'] - unusual['avg_amount']) / unusual['avg_amount']) * 100
        unusual = unusual.sort_values('percent_increase', ascending=False)
    
    return unusual

def calculate_savings_projection(df, monthly_saving_target):
    """
    Calculate savings projection based on current spending and a target savings amount
    
    Args:
        df: DataFrame containing transaction data
        monthly_saving_target: Target monthly savings amount
        
    Returns:
        Dictionary with savings projection metrics
    """
    if df.empty:
        return {
            'possible': False,
            'message': 'No hay suficientes datos para calcular proyecciones.'
        }
    
    # Calculate monthly income and expenses
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.strftime('%Y-%m')
    
    # Group by month and type
    monthly_summary = df.groupby(['month', 'type'])['amount_pesos'].sum().unstack().fillna(0)
    
    if 'Ingreso' not in monthly_summary.columns or 'Gasto' not in monthly_summary.columns:
        return {
            'possible': False,
            'message': 'Se requieren datos de ingresos y gastos para calcular proyecciones.'
        }
    
    # Calculate monthly balance
    monthly_summary['Balance'] = monthly_summary['Ingreso'] - monthly_summary['Gasto']
    
    # Use only recent months data
    num_months = min(6, len(monthly_summary))
    if num_months < 3:
        return {
            'possible': False,
            'message': 'Se necesitan al menos 3 meses de datos para calcular proyecciones confiables.'
        }
    
    recent_summary = monthly_summary.tail(num_months)
    
    # Calculate average monthly income, expenses, and balance
    avg_income = recent_summary['Ingreso'].mean()
    avg_expenses = recent_summary['Gasto'].mean()
    avg_balance = recent_summary['Balance'].mean()
    
    # Check if monthly saving target is achievable
    if avg_balance >= monthly_saving_target:
        # Already meeting the target
        savings_percent = (monthly_saving_target / avg_income) * 100
        expenses_percent = ((avg_expenses) / avg_income) * 100
        
        return {
            'possible': True,
            'message': 'Ya estás alcanzando tu objetivo de ahorro mensual.',
            'avg_income': avg_income,
            'avg_expenses': avg_expenses,
            'avg_balance': avg_balance,
            'target_savings': monthly_saving_target,
            'current_savings_percent': savings_percent,
            'expenses_percent': expenses_percent,
            'suggested_expense_reduction': 0
        }
    else:
        # Calculate how much expenses need to be reduced
        required_reduction = monthly_saving_target - avg_balance
        reduction_percent = (required_reduction / avg_expenses) * 100
        
        # Calculate the new expense target
        new_expense_target = avg_expenses - required_reduction
        new_expense_percent = (new_expense_target / avg_income) * 100
        savings_percent = (monthly_saving_target / avg_income) * 100
        
        return {
            'possible': avg_income > new_expense_target,
            'message': 'Para alcanzar tu objetivo de ahorro mensual, necesitas reducir gastos.' if avg_income > new_expense_target
                       else 'Tu objetivo de ahorro no es alcanzable con tus ingresos actuales.',
            'avg_income': avg_income,
            'avg_expenses': avg_expenses,
            'avg_balance': avg_balance,
            'target_savings': monthly_saving_target,
            'suggested_expense_reduction': required_reduction,
            'reduction_percent': reduction_percent,
            'new_expense_target': new_expense_target,
            'new_expense_percent': new_expense_percent,
            'savings_percent': savings_percent
        }

def analyze_expense_trends(df):
    """
    Analyze expense trends over time by category
    
    Args:
        df: DataFrame containing transaction data
        
    Returns:
        Dictionary with trend analysis results
    """
    if df.empty:
        return {}
    
    # Filter to only include expenses
    expenses_df = df[df['type'] == 'Gasto'].copy()
    
    if expenses_df.empty:
        return {}
    
    # Convert date to datetime if not already
    expenses_df['date'] = pd.to_datetime(expenses_df['date'])
    
    # Group by month and category
    expenses_df['month'] = expenses_df['date'].dt.strftime('%Y-%m')
    monthly_by_category = expenses_df.groupby(['month', 'category'])['amount_pesos'].sum().reset_index()
    
    # Get unique categories and months
    categories = expenses_df['category'].unique()
    unique_months = sorted(monthly_by_category['month'].unique())
    
    if len(unique_months) < 3:
        return {}  # Not enough data for trend analysis
    
    # Calculate trends for each category
    trends = {}
    
    for category in categories:
        cat_data = monthly_by_category[monthly_by_category['category'] == category]
        cat_data = cat_data.sort_values('month')
        
        if len(cat_data) > 1:
            # Simple linear regression to determine trend
            x = np.arange(len(cat_data))
            y = cat_data['amount_pesos'].values
            
            if len(x) > 0 and len(y) > 0:
                z = np.polyfit(x, y, 1)
                slope = z[0]
                
                # Determine trend direction
                if slope > 0:
                    direction = 'up'
                elif slope < 0:
                    direction = 'down'
                else:
                    direction = 'stable'
                
                # Calculate average monthly change as percentage
                avg_value = cat_data['amount_pesos'].mean()
                if avg_value > 0:
                    monthly_pct_change = (slope / avg_value) * 100
                else:
                    monthly_pct_change = 0
                
                # Determine strength of trend
                if abs(monthly_pct_change) < 3:
                    strength = 'weak'
                elif abs(monthly_pct_change) < 10:
                    strength = 'moderate'
                else:
                    strength = 'strong'
                
                # Add to results
                trends[category] = {
                    'direction': direction,
                    'monthly_change_percent': monthly_pct_change,
                    'strength': strength,
                    'avg_monthly_amount': avg_value
                }
    
    # Sort trends by strength and direction
    increasing_trends = {k: v for k, v in trends.items() 
                        if v['direction'] == 'up' and v['strength'] != 'weak'}
    decreasing_trends = {k: v for k, v in trends.items() 
                        if v['direction'] == 'down' and v['strength'] != 'weak'}
    
    # Sort by percentage change
    increasing_trends = dict(sorted(increasing_trends.items(), 
                                  key=lambda x: x[1]['monthly_change_percent'], 
                                  reverse=True))
    decreasing_trends = dict(sorted(decreasing_trends.items(), 
                                   key=lambda x: x[1]['monthly_change_percent']))
    
    return {
        'increasing': increasing_trends,
        'decreasing': decreasing_trends,
        'all_trends': trends
    }