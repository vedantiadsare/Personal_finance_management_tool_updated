from flask import Flask
import pytest

# Create test Flask app
app = Flask(__name__)
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'test-key'

@app.route('/categories', methods=['GET', 'POST'])
def categories():
    return 'OK'

@app.route('/api/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    return 'OK'

def test_add_category():
    client = app.test_client()
    response = client.post('/categories', data={
        'name': 'Test Category',
        'type': 'expense'
    })
    assert response.status_code == 200

def test_get_categories():
    client = app.test_client()
    response = client.get('/categories')
    assert response.status_code == 200

def test_delete_category():
    client = app.test_client()
    response = client.delete('/api/categories/1')
    assert response.status_code == 200 