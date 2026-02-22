def test_admin_users(client):
    response = client.get('/admin/users')
    assert response.status_code in [200, 401, 403]


def test_admin_predictions(client):
    response = client.get('/admin/predictions')
    assert response.status_code in [200, 401, 403]
