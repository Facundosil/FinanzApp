import pandas as pd
from collections import Counter
import re

def get_category_suggestions(username, df, description):
    """
    Suggests categories for a new transaction based on previous transactions with similar descriptions.
    
    Args:
        username: The username
        df: DataFrame containing user transactions
        description: The description of the new transaction
        
    Returns:
        A dictionary with suggested categories and confidence scores
    """
    # If no description or dataframe is empty, return empty suggestions
    if not description or df.empty:
        return {}
    
    # Normalize the description (lowercase, remove special chars)
    normalized_description = re.sub(r'[^\w\s]', ' ', description.lower())
    
    # Extract all words from the description that are at least 3 chars long
    words = [word for word in normalized_description.split() if len(word) >= 3]
    
    if not words:
        return {}
    
    # Find similar transactions using keywords
    matches = {}
    
    # For each transaction, check if any of its description words match the new description
    for idx, row in df.iterrows():
        # Skip transactions without descriptions
        if pd.isna(row['description']) or not row['description']:
            continue
            
        # Normalize existing transaction description
        existing_desc = re.sub(r'[^\w\s]', ' ', row['description'].lower())
        existing_words = set([word for word in existing_desc.split() if len(word) >= 3])
        
        # Calculate a similarity score based on word matches
        common_words = set(words).intersection(existing_words)
        
        if common_words:
            # The score is the number of matching words divided by the total unique words
            score = len(common_words) / len(set(words).union(existing_words))
            
            # Only consider matches with a minimum score
            if score >= 0.2:  # Threshold for similarity
                category_key = (row['type'], row['category'])
                
                if category_key not in matches:
                    matches[category_key] = []
                    
                matches[category_key].append({
                    'score': score,
                    'transaction_id': row['id'],
                    'description': row['description'],
                    'payment_method': row['payment_method'],
                    'fixed_expense': row['fixed_expense'],
                    'amount': row['amount'],
                    'currency': row['currency']
                })
    
    # Aggregate scores and count occurrences for each category
    suggestions = {}
    for (type_val, category), match_list in matches.items():
        # Calculate the average score and count the number of matches
        avg_score = sum(match['score'] for match in match_list) / len(match_list)
        count = len(match_list)
        
        # Find the most common payment method
        payment_methods = [match['payment_method'] for match in match_list 
                          if pd.notna(match['payment_method'])]
        common_payment_method = Counter(payment_methods).most_common(1)[0][0] if payment_methods else None
        
        # Determine if it's likely a fixed expense
        fixed_values = [match['fixed_expense'] for match in match_list 
                       if pd.notna(match['fixed_expense'])]
        is_fixed = sum(fixed_values) / len(fixed_values) > 0.5 if fixed_values else False
        
        # Store the suggestion
        suggestions[(type_val, category)] = {
            'score': avg_score * (1 + 0.1 * min(count, 10)),  # Boost score based on frequency (capped at 10)
            'count': count,
            'payment_method': common_payment_method,
            'fixed_expense': is_fixed
        }
    
    # Convert to a sorted list of dictionaries for easier consumption
    result = []
    for (type_val, category), data in suggestions.items():
        result.append({
            'type': type_val,
            'category': category,
            'score': data['score'],
            'count': data['count'],
            'payment_method': data['payment_method'],
            'fixed_expense': data['fixed_expense']
        })
    
    # Sort by score in descending order
    result.sort(key=lambda x: x['score'], reverse=True)
    
    return result


def suggest_transaction_details(username, df, description):
    """
    Suggest full transaction details based on similar past transactions.
    
    Args:
        username: The username
        df: DataFrame containing user transactions
        description: The description of the new transaction
        
    Returns:
        A dictionary with suggested transaction details
    """
    suggestions = get_category_suggestions(username, df, description)
    
    if not suggestions:
        return {}
    
    # Get the top suggestion
    top_suggestion = suggestions[0]
    
    # Return a transaction template with suggested values
    return {
        'type': top_suggestion['type'],
        'category': top_suggestion['category'],
        'payment_method': top_suggestion['payment_method'],
        'fixed_expense': top_suggestion['fixed_expense'],
        'confidence': min(top_suggestion['score'], 1.0)  # Cap confidence at 1.0
    }