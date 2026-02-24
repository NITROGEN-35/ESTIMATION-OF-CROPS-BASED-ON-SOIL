"# ESTIMATION-OF-CROPS-BASED-ON-SOIL"

## Testing 🧪

This project uses **pytest** for unit & endpoint tests and **pytest-cov** for coverage reports. Two complementary approaches are applied:

1. **Black‑box testing** – exercise the Flask API via the `client` fixture. The existing tests in `backend/tests` call each route with valid/invalid data and assert on status codes and JSON bodies.
2. **White‑box testing** – import and call internal functions directly so you can hit every branch, loop and error path. For example, `calculate_soil_score` has separate branches for pH, temperature and NPK ranges, and `predict_crop` handles tie‑breaking logic.

### Running tests

```bash
# from project root; make sure virtualenv is activated
cd backend
PYTHONPATH=. python -m pytest --cov=backend --cov-report=term-missing
```

The `--cov-report=term-missing` flag prints out which lines were not executed. You can also generate an HTML report:

```bash
python -m pytest --cov=backend --cov-report=html
# open backend/htmlcov/index.html in a browser
```

A fresh test file (`backend/tests/test_app_logic.py`) demonstrates the structure of thorough black/white‑box tests along with database mocking and parameterized checks.

#### Module testing

`test_app_logic.py` and the other Python unit tests are essentially _module tests_ – they import functions and classes from your backend modules (`app.py`, `ml_core.py`, etc.) and call them directly. Whenever you write a new helper or refactor logic, add a corresponding unit test that exercises its edge cases. This is the classic white‑box testing style and ensures that every line of code inside your modules is executed by the test suite.

#### GUI / frontend testing

The repository also contains several static web pages (`indexl.html`, `dashboard.html`, `admin.html`, etc.). To validate the user interface, you can use a browser automation toolkit such as **Selenium** or **Playwright**.

Below is a minimal Selenium example – save it as `backend/tests/test_gui.py` and run it with `pytest` after installing the `selenium` package and a webdriver (ChromeDriver, geckodriver, etc.).

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import pytest

@pytest.fixture(scope="module")
def driver():
    d = webdriver.Chrome()  # ensure chromedriver is on your PATH
    yield d
    d.quit()


def test_homepage_loads(driver):
    # point at the file or, if you prefer, start the flask server and use http://localhost:5000
    driver.get("file:///" + __file__.rpartition("/")[0] + "/../indexl.html")
    assert "Crop Estimator" in driver.title
    assert driver.find_element(By.NAME, "N")
```

You can expand this script to fill out forms, click buttons, and verify that the UI behaves correctly. For full end‑to‑end tests, start the Flask backend in a subprocess and have the browser visit `http://127.0.0.1:5000`.

### Writing more tests

- Add tests for each new function you create.
- Use `monkeypatch` to stub `get_db_connection`, `get_current_user`, or any external dependency.
- Parametrize inputs to exercise boundary values and error messages.
- Ensure you hit each `if`/`elif`/`except` block – coverage tools will show missing branches.

### Tools

- `pytest-cov`: coverage measurement
- `black`, `flake8` (optional): enforce styling/quality
- `bandit` (optional): static security analysis

By combining these techniques you can drive line‑coverage up to 100 % and satisfy both black‑box (API) and white‑box (code‑aware) testing requirements.
