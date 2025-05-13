from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import random
from flask import Response
import io
import csv
from gemini_helper import analyze_transactions_csv
import os, csv
from flask import request, jsonify
import re
from datetime import datetime
import dateparser
import json
import traceback

# Loading environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')


# Initialize extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database connection function
def get_db_connection():
    try:
        # Debug prints to check environment variables
        print(f"DB_HOST: {os.getenv('DB_HOST')}")
        print(f"DB_USER: {os.getenv('DB_USER')}")
        print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
        print(f"DB_NAME: {os.getenv('DB_NAME')}")
        
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'finance1_db')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Initializing database
def init_db():
    try:
        connection = get_db_connection()
        if not connection:
            return None
            
        cursor = connection.cursor()
        
        # Creating users table 
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Creating categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(50) NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Creating transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                amount DECIMAL(10, 2) NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                user_id INT NOT NULL,
                category_id INT NOT NULL,
                payment_method VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            )
        ''')
        
        # Creating budget_goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_goals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                category_id INT NOT NULL,
                target_amount DECIMAL(10, 2) NOT NULL,
                period VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly', 'yearly'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_category_period (user_id, category_id, period)
            )
        ''')
        
        connection.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

# Initialize database
init_db()

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']
        self.created_at = user_data.get('created_at', datetime.utcnow())

@login_manager.user_loader
def load_user(user_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                return User(user_data)
        except Exception as e:
            print(f"Error loading user: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if connection:
                connection.close()
    return None

# Root route(index.html)
@app.route('/')
def index():
    return render_template('index.html')

# Page routes(login.html, register.html)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user_data = cursor.fetchone()
                
                if user_data and bcrypt.check_password_hash(user_data['password_hash'], password):
                    user = User(user_data)
                    login_user(user)
                    flash('You have been logged in successfully!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password', 'danger')
            except Exception as e:
                print(f"Error during login: {e}")
                flash('An error occurred during login. Please try again.', 'danger')
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if connection:
                    connection.close()
        else:
            flash('Database connection error. Please try again later.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('transactions'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # To Check password strength
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return render_template('register.html')

        if not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            flash('Password must include at least one uppercase letter, one lowercase letter, one number, and one special character', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)

                # Check if username exists
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash('Username already exists', 'danger')
                    return render_template('register.html')

                # Check if email exists
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('Email already exists', 'danger')
                    return render_template('register.html')

                # Creating new user
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, created_at) VALUES (%s, %s, %s, %s)",
                    (username, email, hashed_password, datetime.utcnow())
                )
                connection.commit()

                # Get the user ID of the newly created user
                user_id = cursor.lastrowid

                # Add default categories for the new user
                default_income_categories = [
                    'Salary or Wages', 
                    'Business Income', 
                    'Investments', 
                    'Rental Income', 
                    'Gifts', 
                    'Bonuses or Commissions', 
                    'Side Hustles', 
                    'Pension or Retirement Funds', 
                    'Other Income'
                ]

                default_expense_categories = [
                    'Housing', 
                    'Food and Groceries', 
                    'Transportation', 
                    'Healthcare', 
                    'Personal and Household', 
                    'Entertainment and Leisure', 
                    'Debt and Financial Obligations', 
                    'Savings and Investments', 
                    'Insurance', 
                    'Miscellaneous'
                ]

                for category_name in default_income_categories:
                    cursor.execute(
                        "INSERT INTO categories (name, type, user_id, created_at) VALUES (%s, %s, %s, %s)",
                        (category_name, 'income', user_id, datetime.utcnow())
                    )

                for category_name in default_expense_categories:
                    cursor.execute(
                        "INSERT INTO categories (name, type, user_id, created_at) VALUES (%s, %s, %s, %s)",
                        (category_name, 'expense', user_id, datetime.utcnow())
                    )

                connection.commit()
                flash('Your account has been created! You can now log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                print(f"Error during registration: {e}")
                flash('An error occurred during registration. Please try again.', 'danger')
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if connection:
                    connection.close()
        else:
            flash('Database connection error. Please try again later.', 'danger')

    return render_template('register.html')

# Transactions route(transactions.html)
@app.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            try:
                # Debug logging
                print("Form data received:", request.form)
                
                amount = float(request.form['amount'])
                description = request.form['description']
                date = request.form['date']
                category_id = int(request.form['category_id'])
                transaction_type = request.form.get('transaction_type', 'expense')  # Default to expense if not provided
                payment_method = request.form.get('payment_method', 'Other')
                
                print(f"Parsed values - Amount: {amount}, Description: {description}, Date: {date}, Category ID: {category_id}, Type: {transaction_type}, Payment Method: {payment_method}")
                
                if amount <= 0:
                    flash('Amount must be greater than 0', 'danger')
                    return redirect(url_for('transactions'))
                
                if not description.strip():
                    flash('Description cannot be empty', 'danger')
                    return redirect(url_for('transactions'))
                
                # Verify category exists and belongs to user
                cursor.execute('''
                    SELECT id, type FROM categories 
                    WHERE id = %s AND user_id = %s
                ''', (category_id, current_user.id))
                category = cursor.fetchone()
                if not category:
                    flash('Invalid category selected', 'danger')
                    return redirect(url_for('transactions'))
                
                # Verify category type matches transaction type
                if category['type'] != transaction_type:
                    flash('Category type does not match transaction type', 'danger')
                    return redirect(url_for('transactions'))
                
                # Add the transaction
                cursor.execute('''
                    INSERT INTO transactions (amount, description, date, user_id, category_id, payment_method)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (amount, description, date, current_user.id, category_id, payment_method))
                
                connection.commit()
                flash('Transaction added successfully!', 'success')
                return redirect(url_for('transactions'))
                
            except ValueError as e:
                print(f"ValueError: {str(e)}")
                flash('Invalid input format. Please check your entries.', 'danger')
                return redirect(url_for('transactions'))
            except Exception as e:
                print(f"Error adding transaction: {str(e)}")
                flash(f'Error adding transaction: {str(e)}', 'danger')
                return redirect(url_for('transactions'))
        
        # Get categories for the dropdown
        cursor.execute('SELECT * FROM categories WHERE user_id = %s', (current_user.id,))
        categories = cursor.fetchall()
        
        # Get transactions
        cursor.execute('''
            SELECT t.*, c.name as category_name, c.type as category_type
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = %s
            ORDER BY t.date DESC, t.created_at DESC
        ''', (current_user.id,))
        transactions = cursor.fetchall()
        
        return render_template('transactions.html', transactions=transactions, categories=categories)
        
    except Exception as e:
        print(f"Error in transactions route: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# API routes(transactions.html)
@app.route('/api/transactions/<int:transaction_id>', methods=['GET', 'DELETE', 'PUT'])
@login_required
def transaction_api(transaction_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'GET':
            # Get transaction details
            cursor.execute("""
                SELECT t.*, c.name as category_name, c.type as category_type
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.id = %s AND t.user_id = %s
            """, (transaction_id, current_user.id))
            transaction = cursor.fetchone()
            
            if transaction:
                # Format the date properly
                date_str = transaction['date']
                if not isinstance(date_str, str):
                    date_str = date_str.strftime('%Y-%m-%d')
                
                return jsonify({
                    'id': transaction['id'],
                    'amount': transaction['amount'],
                    'description': transaction['description'],
                    'date': date_str,
                    'category_id': transaction['category_id'],
                    'category_name': transaction['category_name'],
                    'category_type': transaction['category_type'],
                    'payment_method': transaction.get('payment_method', 'Other')
                })
            else:
                return jsonify({'error': 'Transaction not found'}), 404
        
        elif request.method == 'DELETE':
            # Delete transaction
            cursor.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", 
                         (transaction_id, current_user.id))
            connection.commit()
            return jsonify({'message': 'Transaction deleted successfully'})
        
        elif request.method == 'PUT':
            # Update the transaction
            data = request.get_json()
            
            # Verify the transaction exists and belongs to the user
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE id = %s AND user_id = %s
            """, (transaction_id, current_user.id))
            transaction = cursor.fetchone()
            
            if not transaction:
                return jsonify({'error': 'Transaction not found'}), 404
            
            # Update the transaction
            cursor.execute("""
                UPDATE transactions 
                SET amount = %s, 
                    description = %s, 
                    date = %s, 
                    category_id = %s,
                    payment_method = %s
                WHERE id = %s AND user_id = %s
            """, (
                data['amount'],
                data['description'],
                data['date'],
                data['category_id'],
                data.get('payment_method', 'Other'),
                transaction_id,
                current_user.id
            ))
            
            connection.commit()
            return jsonify({'message': 'Transaction updated successfully'}), 200
    
    except Exception as e:
        print(f"Error in transaction API: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()


# Categories route(categories.html)
@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Handle category creation
            name = request.form.get('name')
            category_type = request.form.get('type')
            
            cursor.execute(
                "INSERT INTO categories (name, type, user_id, created_at) VALUES (%s, %s, %s, %s)",
                (name, category_type, current_user.id, datetime.utcnow())
            )
            connection.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('categories'))
        
        # Get all categories
        cursor.execute("SELECT * FROM categories WHERE user_id = %s ORDER BY type, name", (current_user.id,))
        categories_list = cursor.fetchall()
        
        return render_template('categories.html', categories=categories_list)
    except Exception as e:
        print(f"Error in categories page: {e}")
        flash('Error loading categories', 'danger')
        return redirect(url_for('transactions'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

# Profile route(profile.html)
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Handle profile update
            username = request.form.get('username')
            email = request.form.get('email')
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            
            # Verify current password
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (current_user.id,))
            user_data = cursor.fetchone()
            
            if not bcrypt.check_password_hash(user_data['password_hash'], current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('profile'))
            
            # Update user information
            update_fields = []
            update_values = []
            
            if username and username != current_user.username:
                # Check if username is already taken
                cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (username, current_user.id))
                if cursor.fetchone():
                    flash('Username is already taken', 'danger')
                    return redirect(url_for('profile'))
                update_fields.append("username = %s")
                update_values.append(username)
            
            if email and email != current_user.email:
                # Check if email is already taken
                cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, current_user.id))
                if cursor.fetchone():
                    flash('Email is already taken', 'danger')
                    return redirect(url_for('profile'))
                update_fields.append("email = %s")
                update_values.append(email)
            
            if new_password:
                update_fields.append("password_hash = %s")
                update_values.append(bcrypt.generate_password_hash(new_password).decode('utf-8'))
            
            if update_fields:
                update_values.append(current_user.id)
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(query, tuple(update_values))
                connection.commit()
                
                # Update current user object
                if username:
                    current_user.username = username
                if email:
                    current_user.email = email
                
                flash('Profile updated successfully', 'success')
                return redirect(url_for('profile'))
        
        # Get user data for display
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user.id,))
        user_data = cursor.fetchone()
        
        return render_template('profile.html', user=user_data)
    
    except Exception as e:
        print(f"Error in profile page: {e}")
        flash('Error updating profile', 'danger')
        return redirect(url_for('profile'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

# Delete profile route(delete_profile.html)
@app.route('/delete_profile', methods=['POST'])
@login_required
def delete_profile():
    user_id = current_user.id
    connection = get_db_connection()
    if not connection:
        flash('Database connection error. Could not delete profile.', 'danger')
        return redirect(url_for('profile'))
    
    try:
        cursor = connection.cursor()
        
        # Start transaction
        connection.start_transaction()
        
        # Delete all user data in the correct order to maintain referential integrity
        # 1. Delete transactions (depends on categories)
        cursor.execute("DELETE FROM transactions WHERE user_id = %s", (user_id,))
        
        # 2. Delete budget goals (depends on categories)
        cursor.execute("DELETE FROM budget_goals WHERE user_id = %s", (user_id,))
        
        # 3. Delete categories (depends on users)
        cursor.execute("DELETE FROM categories WHERE user_id = %s", (user_id,))
        
        # 4. Delete notifications if they exist
        try:
            cursor.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,))
        except Exception:
            # Ignore if notifications table doesn't exist
            pass
        
        # 5. Finally, delete the user
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        # Commit the transaction
        connection.commit()
        
        # Logout the user
        logout_user()
        
        flash('Your account and all associated data have been permanently deleted.', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        # Rollback in case of any error
        connection.rollback()
        print(f"Error deleting profile for user {user_id}: {e}")
        flash('An error occurred while deleting your profile. Please try again.', 'danger')
        return redirect(url_for('profile'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

# Logout route(logout.html)
@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# API routes for transaction and category management
@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (transaction_id, current_user.id))
        connection.commit()
        return jsonify({'message': 'Transaction deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting transaction: {e}")
        return jsonify({'error': 'Error deleting transaction'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

# Delete category route(delete_category.html)
@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("DELETE FROM categories WHERE id = %s AND user_id = %s", (category_id, current_user.id))
        connection.commit()
        return jsonify({'message': 'Category deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting category: {e}")
        return jsonify({'error': 'Error deleting category'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

# Dashboard route(dashboard.html)
@app.route('/dashboard')
@login_required
def dashboard():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get total income and expenses
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN c.type = 'income' THEN t.amount ELSE 0 END) as total_income,
                    SUM(CASE WHEN c.type = 'expense' THEN t.amount ELSE 0 END) as total_expenses
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = %s
            ''', (current_user.id,))
            totals = cursor.fetchone()
            
            # Get monthly data for charts
            cursor.execute('''
                SELECT 
                    DATE_FORMAT(t.date, '%%Y-%%m') as month,
                    SUM(CASE WHEN c.type = 'income' THEN t.amount ELSE 0 END) as income,
                    SUM(CASE WHEN c.type = 'expense' THEN t.amount ELSE 0 END) as expenses
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = %s
                GROUP BY DATE_FORMAT(t.date, '%%Y-%%m')
                ORDER BY month DESC
                LIMIT 12
            ''', (current_user.id,))
            monthly_data = cursor.fetchall()
            
            # Calculate monthly savings
            if monthly_data:
                latest_month = monthly_data[0]
                monthly_savings = (latest_month.get('income', 0) or 0) - (latest_month.get('expenses', 0) or 0)
            else:
                monthly_savings = 0
            
            # Get recent transactions
            cursor.execute('''
                SELECT t.*, c.name as category_name, c.type as category_type
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = %s
                ORDER BY t.date DESC, t.created_at DESC
                LIMIT 5
            ''', (current_user.id,))
            recent_transactions = cursor.fetchall()
        
            # Get category breakdown
            cursor.execute('''
                SELECT 
                    c.name,
                    c.type,
                    SUM(t.amount) as total,
                    COUNT(*) as count,
                    ROUND(
                        (SUM(t.amount) / NULLIF(
                            (SELECT SUM(amount) 
                            FROM transactions t2 
                            JOIN categories c2 ON t2.category_id = c2.id 
                            WHERE t2.user_id = %s AND c2.type = c.type), 0
                        ) * 100
                    ), 2) as percentage
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = %s
                GROUP BY c.id, c.name, c.type
                HAVING total > 0
                ORDER BY total DESC
            ''', (current_user.id, current_user.id))
            categories = cursor.fetchall()
            
            # Separate income and expense categories
            income_categories = [c for c in categories if c['type'] == 'income']
            expense_categories = [c for c in categories if c['type'] == 'expense']
            
            # Get budget information
            cursor.execute('''
                SELECT c.id, c.name, 
                       COALESCE(g.target_amount, 0) as target_amount,
                       COALESCE(g.period, 'monthly') as period,
                       COALESCE(SUM(t.amount), 0) as spent,
                       MIN(t.date) as first_transaction,
                       MAX(t.date) as last_transaction
                FROM categories c
                LEFT JOIN budget_goals g ON c.id = g.category_id AND g.user_id = %s
                LEFT JOIN transactions t ON c.id = t.category_id AND t.user_id = %s
                WHERE c.user_id = %s
                GROUP BY c.id, c.name, g.target_amount, g.period
                ORDER BY c.name
            ''', (current_user.id, current_user.id, current_user.id))
            
            budget_categories = cursor.fetchall()
            
            # Get payment method distribution
            cursor.execute('''
                SELECT payment_method, COUNT(*) as count
                FROM transactions
                WHERE user_id = %s
                GROUP BY payment_method
            ''', (current_user.id,))
            payment_method_stats = cursor.fetchall()
            
            # Add budget notifications
            for category in budget_categories:
                if category['target_amount'] > 0:
                    # Calculate actual percentage for notifications
                    actual_percentage = (category['spent'] / category['target_amount']) * 100
                    
                    # Calculate date range based on period
                    today = datetime.now().date()
                    if category['period'] == 'weekly':
                        start_of_period = today - timedelta(days=today.weekday())
                        end_of_period = start_of_period + timedelta(days=6)
                        category['date_range'] = f"{start_of_period.strftime('%d %b')} - {end_of_period.strftime('%d %b %Y')}"
                    elif category['period'] == 'monthly':
                        start_of_period = today.replace(day=1)
                        end_of_period = (start_of_period + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                        category['date_range'] = f"{start_of_period.strftime('%d %b')} - {end_of_period.strftime('%d %b %Y')}"
                    elif category['period'] == 'yearly':
                        start_of_period = today.replace(month=1, day=1)
                        end_of_period = today.replace(month=12, day=31)
                        category['date_range'] = f"{start_of_period.strftime('%d %b %Y')} - {end_of_period.strftime('%d %b %Y')}"
                    else:  # daily
                        start_of_period = end_of_period = today
                        category['date_range'] = today.strftime('%d %b %Y')
                    
                    # Query spent for this category and period
                    cursor.execute('''
                        SELECT COALESCE(SUM(amount), 0) as spent
                        FROM transactions
                        WHERE user_id = %s AND category_id = %s AND date >= %s AND date <= %s
                    ''', (current_user.id, category['id'], start_of_period, end_of_period))
                    spent_result = cursor.fetchone()
                    category['spent'] = spent_result['spent'] if spent_result else 0
                    category['remaining'] = category['target_amount'] - category['spent']
                    if category['target_amount'] > 0:
                        # Calculate actual percentage for notifications
                        actual_percentage = (category['spent'] / category['target_amount']) * 100
                        # Cap the percentage at 100% for the progress bar
                        category['percentage'] = min(100, actual_percentage)
                        # Add budget notifications
                        if actual_percentage >= 90:
                            messages_90 = [
                                'Budget Alert: You have reached 90% of your budget limit. Please review your spending.',
                                'Budget Warning: 90% of your allocated budget has been utilized. Consider adjusting your expenses.',
                                'Budget Notification: Your spending has reached 90% of the budget threshold.',
                                'Budget Alert: You are approaching your budget limit with 90% utilization.'
                            ]
                            if category['spent'] > category['target_amount']:
                                amount_exceeded = category['spent'] - category['target_amount']
                                flash(f'Budget Alert! {random.choice(messages_90)} You\'ve exceeded your {category["period"]} budget for {category["name"]} ({category["date_range"]}) by ₹{amount_exceeded:.2f}!', 'budget')
                            else:
                                flash(f'Budget Alert! {random.choice(messages_90)} You\'ve spent ₹{category["spent"]:.2f} out of ₹{category["target_amount"]:.2f} for {category["name"]} ({category["date_range"]})!', 'budget')
                        elif actual_percentage >= 80:
                            messages_80 = [
                                'Budget Notice: You have utilized 80% of your budget. Please monitor your spending carefully.',
                                'Budget Update: 80% of your budget has been spent. Consider reviewing your expenses.',
                                'Budget Alert: Your spending has reached 80% of the allocated budget.',
                                'Budget Warning: You are approaching 80% of your budget limit.'
                            ]
                            flash(f'Budget Alert! {random.choice(messages_80)} You\'ve spent ₹{category["spent"]:.2f} out of ₹{category["target_amount"]:.2f} for {category["name"]} ({category["date_range"]})!', 'budget')
                        elif actual_percentage >= 50:
                            messages_50 = [
                                'Budget Update: You have spent more than 50% of your allocated budget.',
                                'Budget Notice: More than half of your budget has been utilized.',
                                'Budget Status: You have crossed the halfway point of your budget.',
                                'Budget Update: Spending is now above 50% of your budget.'
                            ]
                            flash(f'Budget Alert! {random.choice(messages_50)} You\'ve spent ₹{category["spent"]:.2f} out of ₹{category["target_amount"]:.2f} for {category["name"]} ({category["date_range"]})', 'budget')
                    else:
                        category['percentage'] = 0
                        category['date_range'] = ''
            
            return render_template('dashboard.html',
                                totals=totals,
                                monthly_data=monthly_data,
                                recent_transactions=recent_transactions,
                                income_categories=income_categories,
                                expense_categories=expense_categories,
                                monthly_savings=monthly_savings,
                                categories=budget_categories,
                                payment_method_stats=payment_method_stats)
            
        except Exception as e:
            print(f"Error in dashboard route: {e}")
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('index'))
        finally:
            if 'cursor' in locals():
                cursor.close()
            if connection:
                connection.close()
    else:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('index'))

# Budget route(budget.html)
@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            category_id = request.form.get('category_id')
            target_amount = request.form.get('target_amount')
            period = request.form.get('period')
            
            if not category_id or not target_amount or not period:
                flash('Please fill in all fields', 'error')
                return redirect(url_for('budget'))
            
            try:
                target_amount = float(target_amount)
                if target_amount <= 0:
                    flash('Target amount must be greater than 0', 'error')
                    return redirect(url_for('budget'))
            except ValueError:
                flash('Invalid target amount', 'error')
                return redirect(url_for('budget'))
            
            # Insert or update the budget goal
            cursor.execute('''
                INSERT INTO budget_goals (user_id, category_id, target_amount, period)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE target_amount = %s, period = %s
            ''', (current_user.id, category_id, target_amount, period, target_amount, period))
            
            connection.commit()
            flash('Budget goal set successfully!', 'success')
            return redirect(url_for('budget'))
        
        # Get all categories with their goals and spending
        cursor.execute('''
            SELECT c.id, c.name, 
                   COALESCE(g.target_amount, 0) as target_amount,
                   COALESCE(g.period, 'monthly') as period,
                   COALESCE(SUM(t.amount), 0) as spent,
                   MIN(t.date) as first_transaction,
                   MAX(t.date) as last_transaction
            FROM categories c
            LEFT JOIN budget_goals g ON c.id = g.category_id AND g.user_id = %s
            LEFT JOIN transactions t ON c.id = t.category_id AND t.user_id = %s
            WHERE c.user_id = %s
            GROUP BY c.id, c.name, g.target_amount, g.period
            ORDER BY c.name
        ''', (current_user.id, current_user.id, current_user.id))
        
        categories = cursor.fetchall()
        
        # Calculate remaining budget and percentage for each category
        for category in categories:
            # Calculate date range based on period
            today = datetime.now().date()
            if category['period'] == 'weekly':
                start_of_period = today - timedelta(days=today.weekday())
                end_of_period = start_of_period + timedelta(days=6)
                category['date_range'] = f"{start_of_period.strftime('%d %b')} - {end_of_period.strftime('%d %b %Y')}"
            elif category['period'] == 'monthly':
                start_of_period = today.replace(day=1)
                end_of_period = (start_of_period + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                category['date_range'] = f"{start_of_period.strftime('%d %b')} - {end_of_period.strftime('%d %b %Y')}"
            elif category['period'] == 'yearly':
                start_of_period = today.replace(month=1, day=1)
                end_of_period = today.replace(month=12, day=31)
                category['date_range'] = f"{start_of_period.strftime('%d %b %Y')} - {end_of_period.strftime('%d %b %Y')}"
            else:  # daily
                start_of_period = end_of_period = today
                category['date_range'] = today.strftime('%d %b %Y')

            # Query spent for this category and period
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as spent
                FROM transactions
                WHERE user_id = %s AND category_id = %s AND date >= %s AND date <= %s
            ''', (current_user.id, category['id'], start_of_period, end_of_period))
            spent_result = cursor.fetchone()
            category['spent'] = spent_result['spent'] if spent_result else 0
            category['remaining'] = category['target_amount'] - category['spent']
            if category['target_amount'] > 0:
                # Calculate actual percentage for notifications
                actual_percentage = (category['spent'] / category['target_amount']) * 100
                # Cap the percentage at 100% for the progress bar
                category['percentage'] = min(100, actual_percentage)
                # Add budget notifications
                if actual_percentage >= 90:
                    messages_90 = [
                        'Budget Alert: You have reached 90% of your budget limit. Please review your spending.',
                        'Budget Warning: 90% of your allocated budget has been utilized. Consider adjusting your expenses.',
                        'Budget Notification: Your spending has reached 90% of the budget threshold.',
                        'Budget Alert: You are approaching your budget limit with 90% utilization.'
                    ]
                    if category['spent'] > category['target_amount']:
                        amount_exceeded = category['spent'] - category['target_amount']
                        flash(f'Budget Alert! {random.choice(messages_90)} You\'ve exceeded your {category["period"]} budget for {category["name"]} ({category["date_range"]}) by ₹{amount_exceeded:.2f}!', 'budget')
                    else:
                        flash(f'Budget Alert! {random.choice(messages_90)} You\'ve spent ₹{category["spent"]:.2f} out of ₹{category["target_amount"]:.2f} for {category["name"]} ({category["date_range"]})!', 'budget')
                elif actual_percentage >= 80:
                    messages_80 = [
                        'Budget Notice: You have utilized 80% of your budget. Please monitor your spending carefully.',
                        'Budget Update: 80% of your budget has been spent. Consider reviewing your expenses.',
                        'Budget Alert: Your spending has reached 80% of the allocated budget.',
                        'Budget Warning: You are approaching 80% of your budget limit.'
                    ]
                    flash(f'Budget Alert! {random.choice(messages_80)} You\'ve spent ₹{category["spent"]:.2f} out of ₹{category["target_amount"]:.2f} for {category["name"]} ({category["date_range"]})!', 'budget')
                elif actual_percentage >= 50:
                    messages_50 = [
                        'Budget Update: You have spent more than 50% of your allocated budget.',
                        'Budget Update: You have spent 50% of your allocated budget.',
                        'Budget Notice: Half of your budget has been utilized.',
                        'Budget Status: 50% of your budget has been spent.',
                        'Budget Update: You have reached the halfway point of your budget.'
                    ]
                    flash(f'Budget Alert! {random.choice(messages_50)} You\'ve spent ₹{category["spent"]:.2f} out of ₹{category["target_amount"]:.2f} for {category["name"]} ({category["date_range"]})', 'budget')
            else:
                category['percentage'] = 0
                category['date_range'] = ''
        
        return render_template('budget.html', categories=categories)
        
    except Exception as e:
        print(f"Error in budget route: {str(e)}")
        flash('An error occurred while processing your request', 'error')
        return redirect(url_for('budget'))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Delete budget route(delete_budget.html)
@app.route('/api/budget/<int:category_id>', methods=['DELETE'])
@login_required
def delete_budget(category_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Delete the budget goal
        cursor.execute('''
            DELETE FROM budget_goals 
            WHERE user_id = %s AND category_id = %s
        ''', (current_user.id, category_id))
        
        connection.commit()
        return '', 204
        
    except Exception as e:
        print(f"Error deleting budget: {str(e)}")
        return jsonify({'error': 'Failed to delete budget goal'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def clean_date_string(spoken_date):
    # Remove suffixes like 'st', 'nd', 'rd', 'th'
    cleaned = re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', spoken_date.lower()).strip()
    return cleaned

def parse_flexible_date(spoken_date):
    cleaned_date = clean_date_string(spoken_date)
    parsed = dateparser.parse(cleaned_date)
    if not parsed:
        raise ValueError(f"Could not parse date from '{spoken_date}'")
    return parsed

# Voice transaction route
@app.route('/voice_transaction', methods=['POST'])
@login_required
def voice_transaction():
    data = request.get_json()
    text = data.get('text', '').lower()

    try:
        match = re.search(r"(income|expense).*?(\d+(\.\d+)?).*?(rupees|rs|₹)?\s*for\s+(.*?)\s+on\s+(.*)", text)
        if not match:
            return jsonify({'success': False, 'message': 'Could not understand. Try saying: "Add expense of 500 rupees for groceries on April 21"'})

        transaction_type = match.group(1)
        amount = float(match.group(2))
        description = match.group(5).strip()
        spoken_date = clean_date_string(match.group(6).strip())  # Clean date here

        date_obj = parse_flexible_date(spoken_date)
        date_obj = date_obj.replace(year=datetime.now().year)
        formatted_date = date_obj.strftime('%Y-%m-%d')

        # Check and insert as before...
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT * FROM categories 
            WHERE user_id = %s AND name = %s AND type = %s
        ''', (current_user.id, description.lower(), transaction_type))
        category = cursor.fetchone()

        if not category:
            return jsonify({'success': False, 'message': f'No matching category found for "{description}" and type "{transaction_type}". Please add it first.'})

        cursor.execute('''
            INSERT INTO transactions (amount, description, date, user_id, category_id)
            VALUES (%s, %s, %s, %s, %s)
        ''', (amount, description, formatted_date, current_user.id, category['id']))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Transaction added successfully via voice!'})

    except Exception as e:
        print(f"Voice transaction error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error processing voice input: {str(e)}'})
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()


def parse_gemini_suggestions(raw_suggestions):
    """
    Parse the suggestions from Gemini AI into a structured format.
    
    This function expects a JSON-like string or a Python dictionary
    containing investment recommendations.
    """
    print("Starting to parse suggestions...")
    if isinstance(raw_suggestions, str):
        raw_suggestions = raw_suggestions.strip()
    if raw_suggestions.startswith("```") and raw_suggestions.endswith("```"):
        raw_suggestions = re.sub(r"^```(?:json)?\s*", "", raw_suggestions)
        raw_suggestions = re.sub(r"\s*```$", "", raw_suggestions)
    
    # If raw_suggestions is empty or None
    if not raw_suggestions:
        print("Warning: Empty suggestions received")
        return []
    
    try:
        # If raw_suggestions is already a dictionary
        if isinstance(raw_suggestions, dict):
            suggestions_dict = raw_suggestions
        # If raw_suggestions is a JSON string
        elif isinstance(raw_suggestions, str):
            # Try to parse as JSON
            try:
                suggestions_dict = json.loads(raw_suggestions)
            except json.JSONDecodeError:
                print("Warning: Could not parse suggestions as JSON")
                # Create a basic structure with the raw text
                return [{
                    "heading": "Investment Recommendations",
                    "subsections": [
                        {
                            "title": "AI Analysis",
                            "content": raw_suggestions
                        }
                    ]
                }]
        else:
            print(f"Warning: Unexpected suggestions type: {type(raw_suggestions)}")
            return []
        
        # Convert to our expected format
        parsed_suggestions = []
        
        # Handle different possible structures
        if "suggestions" in suggestions_dict:
            # Case 1: { "suggestions": [ {...}, {...} ] }
            for section in suggestions_dict["suggestions"]:
                parsed_section = {
                    "heading": section.get("heading", "Investment Section"),
                    "subsections": [],
                    "chart_labels": section.get("chart_labels", []),     
                    "chart_data": section.get("chart_data", []) 
                }
                
                if "subsections" in section:
                    parsed_section["subsections"] = section["subsections"]
                elif "items" in section:
                    parsed_section["subsections"] = section["items"]
                else:
                    # Try to extract key-value pairs as subsections
                    for key, value in section.items():
                        if key != "heading":
                            if isinstance(value, dict):
                                parsed_section["subsections"].append({
                                    "title": key,
                                    "amount": value.get("amount", ""),
                                    "content": value.get("description", "")
                                })
                            else:
                                parsed_section["subsections"].append({
                                    "title": key,
                                    "content": str(value)
                                })
                
                parsed_suggestions.append(parsed_section)
        elif isinstance(suggestions_dict, list):
            # Case 2: [ {...}, {...} ]
            for section in suggestions_dict:
                if isinstance(section, dict):
                    heading = section.get("heading", section.get("title", "Investment Section"))
                    parsed_section = {
                        "heading": heading,
                        "subsections": [],
                        "chart_labels": section.get("chart_labels", []),  
                        "chart_data": section.get("chart_data", []) 
                    }
                    
                    # Extract subsections
                    if "subsections" in section:
                        parsed_section["subsections"] = section["subsections"]
                    elif "items" in section:
                        parsed_section["subsections"] = section["items"]
                    else:
                        # Try to extract key-value pairs as subsections
                        for key, value in section.items():
                            if key not in ["heading", "title"]:
                                if isinstance(value, dict):
                                    parsed_section["subsections"].append({
                                        "title": key,
                                        "amount": value.get("amount", ""),
                                        "content": value.get("description", "")
                                    })
                                else:
                                    parsed_section["subsections"].append({
                                        "title": key,
                                        "content": str(value)
                                    })
                    
                    parsed_suggestions.append(parsed_section)
        else:
            # Case 3: Single suggestion object
            heading = suggestions_dict.get("heading", suggestions_dict.get("title", "Investment Recommendations"))
            parsed_section = {
                "heading": heading,
                "subsections": [],
                "chart_labels": section.get("chart_labels", []),    
                "chart_data": section.get("chart_data", []) 
            }
            
            # Extract subsections
            if "subsections" in suggestions_dict:
                parsed_section["subsections"] = suggestions_dict["subsections"]
            elif "items" in suggestions_dict:
                parsed_section["subsections"] = suggestions_dict["items"]
            else:
                # Try to extract key-value pairs as subsections
                for key, value in suggestions_dict.items():
                    if key not in ["heading", "title"]:
                        if isinstance(value, dict):
                            parsed_section["subsections"].append({
                                "title": key,
                                "amount": value.get("amount", ""),
                                "content": value.get("description", "")
                            })
                        else:
                            parsed_section["subsections"].append({
                                "title": key,
                                "content": str(value)
                            })
            
            parsed_suggestions.append(parsed_section)
        
        print(f"Successfully parsed {len(parsed_suggestions)} suggestion sections")
        return parsed_suggestions
    
    except Exception as e:
        print(f"Error parsing suggestions: {str(e)}")
        traceback.print_exc()
        
        # Return raw text as fallback
        if isinstance(raw_suggestions, str):
            return [{
                "heading": "Investment Recommendations",
                "subsections": [
                    {
                        "title": "AI Analysis",
                        "content": raw_suggestions
                    }
                ]
            }]
        return []

# Suggestions route(suggestions.html)
@app.route('/suggestions')
@login_required
def suggestions():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('transactions'))

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT t.amount, t.description, t.date, c.name as category
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = %s
            ORDER BY t.date DESC
        ''', (current_user.id,))
        transactions = cursor.fetchall()

        # Save CSV
        filename = f"transactions_{current_user.id}.csv"
        filepath = os.path.join("temp", filename)
        os.makedirs("temp", exist_ok=True)

        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Amount', 'Description', 'Date', 'Category'])
                for tx in transactions:
                    writer.writerow([tx['amount'], tx['description'], tx['date'], tx['category']])
            print(f"CSV file saved to: {os.path.abspath(filepath)}")
        except Exception as e:
            print("CSV writing error:", str(e))
            flash("Failed to write transactions to CSV.", "danger")
            return redirect(url_for('transactions'))
        
        try:
            suggestions = analyze_transactions_csv(filepath)
        except Exception as e:
            print("Gemini analysis error:", str(e))
            traceback.print_exc()
            flash("Failed to analyze transactions with Gemini.", "danger")
            return redirect(url_for('transactions'))
                
        os.remove(filepath)  # Clean up

        suggestions_parsed = parse_gemini_suggestions(suggestions)

        # No need for separate chart_configs, we'll include chart data directly in suggestions
        return render_template("suggestions.html", suggestions=suggestions_parsed)
    except Exception as e:
        print("Error analyzing transactions:", str(e))
        traceback.print_exc()
        flash("Failed to analyze transactions.", "danger")
        return redirect(url_for('transactions'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

# Search transaction route
@app.route('/api/transactions/search')
@login_required
def search_transactions():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get unified search query
        search_query = request.args.get('query', '').strip()
        
        # Build the base query
        query = '''
            SELECT t.*, c.name as category_name, c.type as category_type
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = %s
        '''
        params = [current_user.id]
        
        # Add search condition for unified search
        if search_query:
            query += ''' AND (
                t.description LIKE %s 
                OR c.name LIKE %s 
                OR t.payment_method LIKE %s
            )'''
            search_pattern = f'%{search_query}%'
            params.extend([search_pattern, search_pattern, search_pattern])
        
        # Add ordering
        query += ' ORDER BY t.date DESC'
        
        # Execute the query
        cursor.execute(query, tuple(params))
        transactions = cursor.fetchall()
        
        # Convert decimal values to float for JSON serialization
        for transaction in transactions:
            if 'amount' in transaction:
                transaction['amount'] = float(transaction['amount'])
            if 'date' in transaction:
                transaction['date'] = transaction['date'].strftime('%Y-%m-%d')
        
        return jsonify({'transactions': transactions})
        
    except Exception as e:
        print(f"Error in search transactions: {str(e)}")
        return jsonify({'error': 'Error searching transactions'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)