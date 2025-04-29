import os
import csv
import pandas as pd
from datetime import datetime

def get_user_goals_file(username):
    """Get the path to a user's financial goals file"""
    return f"data/{username}_goals.csv"

def create_goals_file_if_not_exists(username):
    """Create goals file if it doesn't exist"""
    file_path = get_user_goals_file(username)
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'id', 'name', 'description', 'type', 'target_amount', 
                'current_amount', 'currency', 'start_date', 'target_date', 
                'category', 'status', 'created_at'
            ])

def load_user_goals(username):
    """Load a user's financial goals"""
    create_goals_file_if_not_exists(username)
    
    file_path = get_user_goals_file(username)
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading user goals: {e}")
        return pd.DataFrame(columns=[
            'id', 'name', 'description', 'type', 'target_amount', 
            'current_amount', 'currency', 'start_date', 'target_date', 
            'category', 'status', 'created_at'
        ])

def get_next_goal_id(username):
    """Get the next available ID for a goal"""
    df = load_user_goals(username)
    if df.empty:
        return 1
    return df['id'].max() + 1

def save_financial_goal(username, goal_data):
    """Save a new financial goal for a user"""
    create_goals_file_if_not_exists(username)
    
    df = load_user_goals(username)
    
    # Add goal ID if not present
    if 'id' not in goal_data or pd.isna(goal_data['id']):
        goal_data['id'] = get_next_goal_id(username)
    
    # Add created_at if not present
    if 'created_at' not in goal_data:
        goal_data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Determine if this is a new goal or an update
    if len(df[df['id'] == goal_data['id']]) > 0:
        # Update existing goal
        df = df[df['id'] != goal_data['id']]
    
    # Append new goal
    df = pd.concat([df, pd.DataFrame([goal_data])], ignore_index=True)
    
    # Save back to file
    file_path = get_user_goals_file(username)
    df.to_csv(file_path, index=False)
    return True

def delete_financial_goal(username, goal_id):
    """Delete a financial goal by ID"""
    create_goals_file_if_not_exists(username)
    
    df = load_user_goals(username)
    
    # Filter out the goal
    df = df[df['id'] != goal_id]
    
    # Save back to file
    file_path = get_user_goals_file(username)
    df.to_csv(file_path, index=False)
    return True

def get_financial_goal_by_id(username, goal_id):
    """Get a financial goal by ID"""
    df = load_user_goals(username)
    goal = df[df['id'] == goal_id]
    if goal.empty:
        return None
    return goal.iloc[0].to_dict()

def update_goal_progress(username, goal_id, new_amount):
    """Update the current amount for a financial goal"""
    goal = get_financial_goal_by_id(username, goal_id)
    if not goal:
        return False
    
    goal['current_amount'] = new_amount
    
    # Update goal status
    if goal['current_amount'] >= goal['target_amount']:
        goal['status'] = 'Completado'
    else:
        goal['status'] = 'En progreso'
    
    return save_financial_goal(username, goal)

def calculate_goal_progress(goal):
    """Calculate progress percentage for a goal"""
    if not goal or 'target_amount' not in goal or 'current_amount' not in goal:
        return 0
    
    target = float(goal['target_amount'])
    current = float(goal['current_amount'])
    
    if target <= 0:
        return 100  # Avoid division by zero
    
    progress = (current / target) * 100
    return min(progress, 100)  # Cap at 100%

def get_goal_types():
    """Get predefined goal types"""
    return [
        "Ahorro", 
        "Inversión", 
        "Compra", 
        "Deuda", 
        "Educación", 
        "Viaje", 
        "Vivienda", 
        "Emergencia", 
        "Otro"
    ]