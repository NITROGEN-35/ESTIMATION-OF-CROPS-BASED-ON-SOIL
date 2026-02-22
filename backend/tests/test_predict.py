def test_predict(client):
    response = client.post('/predict', json={
        "N": 90,
        "P": 40,
        "K": 40,
        "temperature": 25,
        "humidity": 80,
        "ph": 6.5,
        "rainfall": 200
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert "recommended_crop" in json_data
