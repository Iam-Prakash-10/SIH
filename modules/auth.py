from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from modules.database import DatabaseManager

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

class AuthManager:
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_user(self, username, email, password):
        """Create a new user account"""
        try:
            success = self.db.create_user(username, email, password)
            return success
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def login_user_account(self, username, password):
        """Login user and return User object if successful"""
        user_data = self.db.verify_user(username, password)
        if user_data:
            user = User(user_data[0], user_data[1], '')
            login_user(user)
            return user
        return None
    
    def logout_user_account(self):
        """Logout current user"""
        logout_user()
    
    def get_user(self, user_id):
        """Get user by ID for Flask-Login"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(user_data[0], user_data[1], user_data[2])
        return None