from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import unittest
import time
import random
import string
import os

class TestRegister(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.get("http://localhost:5000/register")
        self.wait = WebDriverWait(self.driver, 10)
        os.makedirs("screenshots", exist_ok=True)

    def generate_random_user(self):
        rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"user_{rand}", f"user_{rand}@example.com"

    def fill_registration_form(self, username, email, password, confirm_password):
        driver = self.driver

        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "email").clear()
        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "confirm_password").clear()

        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "email").send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "confirm_password").send_keys(confirm_password)
        driver.find_element(By.NAME, "confirm_password").send_keys(Keys.RETURN)

    def test_valid_registration(self):
        username, email = self.generate_random_user()
        self.fill_registration_form(username, email, "Test@1234", "Test@1234")

        try:
            self.wait.until(EC.url_contains("login"))
            redirected = True
        except:
            redirected = False
            self.driver.save_screenshot(f"screenshots/failed_valid_registration.png")

        self.assertTrue(redirected, "User was not redirected to login page after registration.")

    def test_mismatched_passwords(self):
        username, email = self.generate_random_user()
        self.fill_registration_form(username, email, "Test@1234", "WrongPass")
        time.sleep(1)
        self.assertIn("register", self.driver.current_url.lower())

    def test_invalid_email(self):
        username, _ = self.generate_random_user()
        self.fill_registration_form(username, "invalid-email", "Test@1234", "Test@1234")
        time.sleep(1)
        self.assertIn("register", self.driver.current_url.lower())

    def test_weak_password(self):
        username, email = self.generate_random_user()
        self.fill_registration_form(username, email, "123", "123")
        time.sleep(1)
        self.assertIn("register", self.driver.current_url.lower())

    def test_missing_fields(self):
        self.fill_registration_form("", "", "", "")
        time.sleep(1)
        self.assertIn("register", self.driver.current_url.lower())

    def tearDown(self):
        time.sleep(1)
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()
