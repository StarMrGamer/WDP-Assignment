import unittest
from app import app, db
from models import User, RegistrationCode
from flask import session

class GenConTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            # Create a test admin
            admin = User(username='admin', email='admin@test.com', full_name='Admin', age=30, role='admin')
            admin.set_password('password')
            db.session.add(admin)
            
            # Create a test senior
            senior = User(username='senior', email='senior@test.com', full_name='Senior', age=70, role='senior')
            senior.set_password('password')
            db.session.add(senior)
            
            # Create a test youth
            youth = User(username='youth', email='youth@test.com', full_name='Youth', age=20, role='youth')
            youth.set_password('password')
            db.session.add(youth)
            
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        return self.client.post('/auth/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'GenCon SG', response.data)

    def test_login_senior(self):
        response = self.login('senior', 'password')
        self.assertIn(b'Senior', response.data)
        self.assertIn(b'Dashboard', response.data)

    def test_login_youth(self):
        response = self.login('youth', 'password')
        self.assertIn(b'Youth', response.data)
        self.assertIn(b'Dashboard', response.data)

    def test_senior_dashboard_access(self):
        # Access without login should redirect
        response = self.client.get('/senior/dashboard', follow_redirects=True)
        self.assertIn(b'Please login to access this page', response.data)
        
        # Access with youth login should be denied
        self.login('youth', 'password')
        response = self.client.get('/senior/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied. Senior account required.', response.data)
        
        # Access with senior login should work
        self.logout()
        self.login('senior', 'password')
        response = self.client.get('/senior/dashboard')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
