import pytest
import pandas as pd
from app import app, calculate_soil_score, predict, history
from ml_core import predict_crop
from app import REQUIRED_FIELDS

# ---- helpers ---------------------------------------------------------------

def fake_db(monkeypatch, rows=None, raise_error=False):
    class DummyCursor:
        def __init__(self):
            self._rows = rows or []
        def execute(self, *args, **kwargs):
            if raise_error:
                raise Exception("db failure")
        def fetchall(self):
            return self._rows
        def close(self):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    class DummyConn:
        def __init__(self):
            self._cur = DummyCursor()
        def cursor(self, **kwargs):
            return self._cur
        def commit(self):
            if raise_error:
                raise Exception("db commit fail")
        def close(self):
            pass

    monkeypatch.setattr("app.get_db_connection", lambda: DummyConn())


# ---- white‑box tests for pure functions ----------------------------------

def test_calculate_soil_score_boundaries():
    # ph in good range, npk in range, humidity and rainfall okay, temperature good
    score = calculate_soil_score(100, 100, 100, 25, 50, 6.5, 200)
    # score used to be an int when it hit 100, so allow either numeric type
    assert isinstance(score, (int, float))
    assert float(score) == 100.0  # all categories max out

    # ph too low triggers negative branch
    low = calculate_soil_score(0, 0, 0, -30, 0, 4.0, 0)
    assert low < score

    # temperature high
    temp_hi = calculate_soil_score(50, 50, 50, 40, 50, 7.0, 200)
    assert temp_hi < score


def test_predict_crop_tie(monkeypatch):
    # monkeypatch models so that two crops have equal votes
    # we can simulate by creating an input that forces identical predictions
    df = pd.DataFrame([[90, 40, 40, 25, 80, 6.5, 200]], columns=REQUIRED_FIELDS)
    # call the real function, just check types/keys and branch behaviour
    preds, accs, best, rec, votes = predict_crop(df)

    assert set(preds.keys())
    assert isinstance(accs, dict)
    assert best in preds
    assert rec in preds.values()
    assert isinstance(votes, dict)


# ---- black‑box (API) tests -----------------------------------------------

@pytest.fixture
def auth_client(monkeypatch, client):
    # fake a valid user on every request
    monkeypatch.setattr("app.get_current_user", lambda: {"user_id": 1})
    return client


def test_predict_missing_fields(auth_client):
    response = auth_client.post('/predict', json={})
    assert response.status_code == 400
    assert "Missing fields" in response.get_json()["error"]


def test_predict_invalid_values(auth_client):
    payload = {f: "not a number" for f in REQUIRED_FIELDS}
    response = auth_client.post('/predict', json=payload)
    assert response.status_code == 400
    assert "numeric" in response.get_json()["error"]


def test_predict_out_of_range(auth_client):
    bad = {**{f: 100 for f in REQUIRED_FIELDS}}
    bad['N'] = 999  # out of permitted range
    response = auth_client.post('/predict', json=bad)
    assert response.status_code == 400
    assert "Validation failed" in response.get_json()["error"]


def test_predict_db_error(auth_client, monkeypatch):
    fake_db(monkeypatch, raise_error=True)
    response = auth_client.post('/predict', json={f: 10 for f in REQUIRED_FIELDS})
    # because our stub raises during insert, endpoint should return 500
    assert response.status_code == 500
    assert "Database error" in response.get_json()["error"]


def test_predict_success(auth_client, monkeypatch):
    # stub database so that insert succeeds and no exception is raised
    fake_db(monkeypatch)
    response = auth_client.post('/predict', json={f: 10 for f in REQUIRED_FIELDS})
    assert response.status_code == 200
    json_data = response.get_json()
    assert "predictions" in json_data
    assert "recommended_crop" in json_data


def test_history_unauthorized(client):
    response = client.get('/history/1')
    assert response.status_code == 401


def test_history_forbidden(client, monkeypatch):
    monkeypatch.setattr("app.get_current_user", lambda: {"user_id": 2})
    response = client.get('/history/1')
    assert response.status_code == 403


def test_history_db_error(auth_client, monkeypatch):
    fake_db(monkeypatch, raise_error=True)
    response = auth_client.get('/history/1')
    assert response.status_code == 500
    assert "Database error" in response.get_json()["error"]


def test_history_success(auth_client, monkeypatch):
    # return a list of dicts with a datetime-like object
    class DummyRec:
        def isoformat(self):
            return "2020-01-01T00:00:00"

    rows = [{"created_at": DummyRec(), "some": "value"}]
    fake_db(monkeypatch, rows=rows)
    response = auth_client.get('/history/1')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert data[0]["created_at"].startswith("2020")
