from flask import Flask
import pytest

# Create test Flask app
app = Flask(__name__)

@app.route('/profile', methods=['GET', 'PUT'])
def profile():
    return 'OK'

@app.route('/api/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    return 'OK'

def test_get_profile():
    client = app.test_client()
    response = client.get('/profile')
    assert response.status_code == 200

def test_update_profile():
    client = app.test_client()
    response = client.put('/profile', data={
        'username': 'newusername',
        'email': 'new@example.com'
    })
    assert response.status_code == 200

def test_delete_user():
    client = app.test_client()
    response = client.delete('/api/user/1')
    assert response.status_code == 200 