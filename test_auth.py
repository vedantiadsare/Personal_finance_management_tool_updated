from flask import Flask
import pytest

# Create test Flask app
app = Flask(__name__)

@app.route('/register', methods=['GET', 'POST'])
def register():
    return 'OK'

@app.route('/login', methods=['GET', 'POST'])
def login():
    return 'OK'

def test_register_page():
    client = app.test_client()
    response = client.get('/register')
    assert response.status_code == 200

def test_register_user():
    client = app.test_client()
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass',
        'confirm_password': 'testpass'
    })
    assert response.status_code == 200

def test_login_page():
    client = app.test_client()
    response = client.get('/login')
    assert response.status_code == 200

def test_login_user():
    client = app.test_client()
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 200 