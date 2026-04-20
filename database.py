import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    def __init__(self, db_name='data/comments.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Comments table - NOW WITH USER_ID
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Sentiment results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id INTEGER,
                sentiment TEXT,
                positive_score REAL,
                negative_score REAL,
                neutral_score REAL,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (comment_id) REFERENCES comments (id)
            )
        ''')
        
        # Review queue table - NOW WITH USER_ID
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id INTEGER,
                user_id INTEGER NOT NULL,
                text TEXT,
                ai_sentiment TEXT,
                ai_confidence REAL,
                human_sentiment TEXT,
                reviewed BOOLEAN DEFAULT 0,
                reviewed_at TIMESTAMP,
                reviewer_notes TEXT,
                FOREIGN KEY (comment_id) REFERENCES comments (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")
    
    # ===== USER AUTHENTICATION METHODS =====
    
    def create_user(self, username, password, email=None):
        """Create a new user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            password_hash = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                (username, password_hash, email)
            )
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None  # Username already exists
    
    def get_user_by_username(self, username):
        """Get user by username"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def verify_password(self, username, password):
        """Verify user password"""
        user = self.get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None
    
    # ===== MODIFIED COMMENT METHODS (NOW USER-SPECIFIC) =====
    
    def add_comment(self, text, user_id, source='manual'):
        """Add a new comment for specific user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO comments (text, user_id, source) VALUES (?, ?, ?)',
            (text, user_id, source)
        )
        comment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return comment_id
    
    def add_sentiment_result(self, comment_id, sentiment, pos, neg, neu):
        """Store sentiment analysis result"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sentiment_results 
            (comment_id, sentiment, positive_score, negative_score, neutral_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (comment_id, sentiment, pos, neg, neu))
        conn.commit()
        conn.close()
    
    def get_all_results(self, user_id):
        """Get all comments with sentiment results for specific user"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.text, c.source, c.created_at,
                   sr.sentiment, sr.positive_score, sr.negative_score, sr.neutral_score
            FROM comments c
            LEFT JOIN sentiment_results sr ON c.id = sr.comment_id
            WHERE c.user_id = ?
            ORDER BY c.created_at DESC
        ''', (user_id,))
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    
    def get_statistics(self, user_id):
        """Get sentiment statistics for specific user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
                SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
                AVG(positive_score) as avg_positive,
                AVG(negative_score) as avg_negative
            FROM sentiment_results sr
            JOIN comments c ON sr.comment_id = c.id
            WHERE c.user_id = ?
        ''', (user_id,))
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            'total': stats[0] or 0,
            'positive': stats[1] or 0,
            'negative': stats[2] or 0,
            'neutral': stats[3] or 0,
            'avg_positive': round(stats[4] or 0, 3),
            'avg_negative': round(stats[5] or 0, 3)
        }
    
    # ===== REVIEW QUEUE METHODS (NOW USER-SPECIFIC) =====
    
    def add_to_review_queue(self, comment_id, user_id, text, ai_sentiment, ai_confidence):
        """Add comment to review queue for specific user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO review_queue 
            (comment_id, user_id, text, ai_sentiment, ai_confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (comment_id, user_id, text, ai_sentiment, ai_confidence))
        conn.commit()
        conn.close()
    
    def get_review_queue(self, user_id, reviewed=False):
        """Get comments needing review for specific user"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM review_queue 
            WHERE user_id = ? AND reviewed = ?
            ORDER BY id DESC
        ''', (user_id, 1 if reviewed else 0))
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    
    def submit_human_review(self, review_id, human_sentiment, notes=''):
        """Submit human review for a comment"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE review_queue 
            SET human_sentiment = ?, 
                reviewed = 1, 
                reviewed_at = CURRENT_TIMESTAMP,
                reviewer_notes = ?
            WHERE id = ?
        ''', (human_sentiment, notes, review_id))
        
        # Also update the sentiment_results table
        cursor.execute('''
            UPDATE sentiment_results 
            SET sentiment = ?
            WHERE comment_id = (SELECT comment_id FROM review_queue WHERE id = ?)
        ''', (human_sentiment, review_id))
        
        conn.commit()
        conn.close()
    
    def get_review_statistics(self, user_id):
        """Get review queue statistics for specific user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM review_queue WHERE user_id = ? AND reviewed = 0', (user_id,))
        pending = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM review_queue WHERE user_id = ? AND reviewed = 1', (user_id,))
        completed = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT AVG(CASE 
                WHEN ai_sentiment = human_sentiment THEN 1.0 
                ELSE 0.0 
            END) * 100 as accuracy
            FROM review_queue 
            WHERE user_id = ? AND reviewed = 1 AND human_sentiment IS NOT NULL
        ''', (user_id,))
        accuracy = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'pending': pending,
            'completed': completed,
            'ai_accuracy': round(accuracy, 1)
        }
    
    def clear_all_data(self):
        """Clear all data (useful for testing)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sentiment_results')
        cursor.execute('DELETE FROM review_queue')
        cursor.execute('DELETE FROM comments')
        cursor.execute('DELETE FROM users')
        conn.commit()
        conn.close()
        print("✅ All data cleared!")

# Test the database
if __name__ == "__main__":
    db = Database()
    print("Database setup complete!")
