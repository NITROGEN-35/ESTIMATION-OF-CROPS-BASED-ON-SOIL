def test_register(client):
    response = client.post('/register', json={
        "full_name": "Test User",
        "email": "testuser@gmail.com",
        "password": "123456"
    })
    assert response.status_code in [200, 201, 400]


def test_login(client):
    response = client.post('/login', json={
        "email": "testuser@gmail.com",
        "password": "123456"
    })
    assert response.status_code in [200, 401]
