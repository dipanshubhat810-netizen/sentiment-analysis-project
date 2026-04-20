from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, email=None):
        self.id = id
        self.username = username
        self.email = email
    
    def get_id(self):
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'
