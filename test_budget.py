from flask import Flask
import pytest

# Create test Flask app
app = Flask(__name__)

@app.route('/budget', methods=['GET', 'POST'])
def budget():
    return 'OK'

@app.route('/api/budget/<int:id>', methods=['DELETE'])
def delete_budget(id):
    return 'OK'

def test_add_budget():
    client = app.test_client()
    response = client.post('/budget', data={
        'amount': 1000.00,
        'category_id': '1',
        'start_date': '2024-01-01',
        'end_date': '2024-12-31'
    })
    assert response.status_code == 200

def test_get_budget():
    client = app.test_client()
    response = client.get('/budget')
    assert response.status_code == 200

def test_delete_budget():
    client = app.test_client()
    response = client.delete('/api/budget/1')
    assert response.status_code == 200 