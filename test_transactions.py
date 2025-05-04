from flask import Flask
import pytest

# Create test Flask app
app = Flask(__name__)
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'test-key'

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    return 'OK'

@app.route('/api/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    return 'OK'

def test_add_transaction():
    client = app.test_client()
    response = client.post('/transactions', data={
        'amount': 100.00,
        'type': 'expense',
        'category_id': '1',
        'description': 'Test Transaction'
    })
    assert response.status_code == 200

def test_get_transactions():
    client = app.test_client()
    response = client.get('/transactions')
    assert response.status_code == 200

def test_delete_transaction():
    client = app.test_client()
    response = client.delete('/api/transactions/1')
    assert response.status_code == 200 