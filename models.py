from datetime import datetime
from database import get_db_connection

class User:
    @staticmethod
    def create(username, email, password_hash):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, created_at) VALUES (%s, %s, %s, %s)",
                (username, email, password_hash, datetime.now())
            )
            connection.commit()
            user_id = cursor.lastrowid
            return {'id': user_id, 'username': username, 'email': email}
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_by_id(user_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_by_username(username):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_by_email(email):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

class Category:
    @staticmethod
    def create(name, type, user_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO categories (name, type, user_id) VALUES (%s, %s, %s)",
                (name, type, user_id)
            )
            connection.commit()
            category_id = cursor.lastrowid
            return {'id': category_id, 'name': name, 'type': type, 'user_id': user_id}
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_by_user(user_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM categories WHERE user_id = %s", (user_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_by_id(category_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

class Transaction:
    @staticmethod
    def create(amount, type, category_id, user_id, description='', date=None):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO transactions (amount, type, category_id, user_id, description, date) VALUES (%s, %s, %s, %s, %s, %s)",
                (amount, type, category_id, user_id, description, date or datetime.now())
            )
            connection.commit()
            transaction_id = cursor.lastrowid
            return {
                'id': transaction_id,
                'amount': amount,
                'type': type,
                'category_id': category_id,
                'user_id': user_id,
                'description': description,
                'date': date or datetime.now()
            }
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_by_user(user_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM transactions WHERE user_id = %s", (user_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_by_id(transaction_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM transactions WHERE id = %s", (transaction_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def delete(transaction_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
            connection.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_summary(user_id, start_date=None, end_date=None):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            query = "SELECT type, SUM(amount) as total FROM transactions WHERE user_id = %s"
            params = [user_id]
            
            if start_date:
                query += " AND date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND date <= %s"
                params.append(end_date)
                
            query += " GROUP BY type"
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            
            total_income = sum(row[1] for row in results if row[0] == 'income')
            total_expense = sum(row[1] for row in results if row[0] == 'expense')
            balance = total_income - total_expense
            
            return {
                'total_income': total_income,
                'total_expense': total_expense,
                'balance': balance
            }
        finally:
            cursor.close()
            connection.close() 