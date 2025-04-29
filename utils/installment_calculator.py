import pandas as pd
from datetime import datetime, timedelta
import calendar

def calculate_installment_payments(transaction_data, dollar_rate):
    """
    Calculate the installment payment schedule for a transaction
    
    Args:
        transaction_data: Dictionary with transaction data
        dollar_rate: Current dollar exchange rate
    
    Returns:
        DataFrame with installment payment schedule
    """
    # Extract required data
    amount = float(transaction_data['amount'])
    currency = transaction_data['currency']
    total_installments = int(transaction_data['installments_total'])
    date_str = transaction_data['date']
    
    # Convert to pandas datetime
    start_date = pd.to_datetime(date_str)
    
    # Calculate amount per installment
    installment_amount = amount / total_installments
    
    # Prepare data for installment schedule
    installments = []
    
    for i in range(1, total_installments + 1):
        # Calculate payment date
        payment_date = add_months(start_date, i - 1)
        
        # Calculate peso amount
        if currency == 'USD':
            peso_amount = installment_amount * dollar_rate
        else:
            peso_amount = installment_amount
        
        installments.append({
            'installment_number': i,
            'date': payment_date.strftime('%Y-%m-%d'),
            'amount': installment_amount,
            'currency': currency,
            'amount_pesos': peso_amount,
            'paid': i <= transaction_data.get('installments_paid', 0)
        })
    
    return pd.DataFrame(installments)

def add_months(date, months):
    """Add months to a date, handling month end days correctly"""
    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1
    
    # Get the last day of the month
    last_day = calendar.monthrange(year, month)[1]
    
    # Use the original day or the last day of the month, whichever is smaller
    day = min(date.day, last_day)
    
    return date.replace(year=year, month=month, day=day)

def get_upcoming_installments(username, transactions_df, months_ahead=3):
    """
    Get upcoming installment payments for the next few months
    
    Args:
        username: Username
        transactions_df: DataFrame with transactions
        months_ahead: Number of months to look ahead
    
    Returns:
        DataFrame with upcoming installment payments
    """
    # Filter for credit card transactions with installments
    installment_txns = transactions_df[
        (transactions_df['payment_method'] == 'Tarjeta de Crédito') & 
        (transactions_df['installments_total'] > 1)
    ]
    
    if installment_txns.empty:
        return pd.DataFrame()
    
    # Current date and future cutoff
    now = datetime.now()
    future_cutoff = now + timedelta(days=30*months_ahead)
    
    upcoming = []
    
    for _, txn in installment_txns.iterrows():
        total_installments = int(txn['installments_total'])
        paid_installments = int(txn['installments_paid'])
        
        # Skip if all installments are paid
        if paid_installments >= total_installments:
            continue
        
        # Transaction date
        txn_date = pd.to_datetime(txn['date'])
        
        # Calculate remaining installments
        for i in range(paid_installments + 1, total_installments + 1):
            payment_date = add_months(txn_date, i - 1)
            
            # Skip if payment date is in the past or too far in the future
            if payment_date < now or payment_date > future_cutoff:
                continue
            
            # Amount per installment
            installment_amount = float(txn['amount']) / total_installments
            
            if txn['currency'] == 'USD':
                # For USD transactions, we'll need the current rate
                # This is just an estimate; actual conversion would happen later
                peso_amount = installment_amount * float(txn['exchange_rate'])
            else:
                peso_amount = installment_amount
            
            upcoming.append({
                'transaction_id': txn['id'],
                'description': txn['description'],
                'installment_number': i,
                'total_installments': total_installments,
                'payment_date': payment_date.strftime('%Y-%m-%d'),
                'amount': installment_amount,
                'currency': txn['currency'],
                'amount_pesos': peso_amount
            })
    
    upcoming_df = pd.DataFrame(upcoming)
    if not upcoming_df.empty:
        # Sort by payment date
        upcoming_df = upcoming_df.sort_values('payment_date')
    
    return upcoming_df
