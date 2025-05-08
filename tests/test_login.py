from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import unittest

class TestLogin(unittest.TestCase):

    def setUp(self):
        # Launch Chrome browser
        self.driver = webdriver.Chrome()
        # Maximize window for visibility
        self.driver.maximize_window()
        # Navigate to login page
        self.driver.get("http://localhost:5000/login")

    def test_valid_login(self):
        driver = self.driver
        # Fill in correct username and password
        driver.find_element(By.NAME, "username").send_keys("john123")
        driver.find_element(By.NAME, "password").send_keys("Test@1234")
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

        # Wait for redirection
        time.sleep(2)

        # Assert user is redirected to dashboard
        self.assertIn("dashboard", driver.current_url)
        print("✅ Valid login successful.")

    def test_invalid_login_wrong_password(self):
        driver = self.driver
        # Enter valid username but wrong password
        driver.find_element(By.NAME, "username").send_keys("john123")
        driver.find_element(By.NAME, "password").send_keys("wrongpass")
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

        # Wait for error to appear
        time.sleep(2)

        # Check if the error message is shown
        error_elements = driver.find_elements(By.CLASS_NAME, "alert-danger")
        self.assertTrue(len(error_elements) > 0, "❌ Error alert not displayed for invalid login.")
        print("✅ Invalid login (wrong password) correctly rejected.")

    def test_invalid_login_unknown_user(self):
        driver = self.driver
        # Enter invalid username
        driver.find_element(By.NAME, "username").send_keys("unknownuser")
        driver.find_element(By.NAME, "password").send_keys("anyPassword")
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

        # Wait for error message
        time.sleep(2)

        # Check for error alert
        error_elements = driver.find_elements(By.CLASS_NAME, "alert-danger")
        self.assertTrue(len(error_elements) > 0, "❌ Error alert not displayed for unknown user.")
        print("✅ Invalid login (unknown user) correctly rejected.")

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()
