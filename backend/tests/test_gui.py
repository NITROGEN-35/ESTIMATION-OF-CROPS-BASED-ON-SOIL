# selenium-based GUI test example
from selenium import webdriver
from selenium.webdriver.common.by import By
import pytest

@pytest.fixture(scope="module")
def driver():
    # requires a browser driver (e.g. chromedriver) on PATH
    d = webdriver.Chrome()
    yield d
    d.quit()


def test_homepage_loads(driver):
    # open the static HTML file; change to http://localhost:5000 if running server
    import os
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    html = "file:///" + os.path.join(base, "indexl.html").replace("\\", "/")
    driver.get(html)
    assert "Crop" in driver.title
    # ensure one of the input fields is present
    driver.find_element(By.NAME, "N")
