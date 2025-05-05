from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import unittest

class TestLogin(unittest.TestCase):

    def setUp(self):
        # Launch Chrome browser
        self.driver = webdriver.Chrome()
        # Navigate to your login page
        self.driver.get("http://localhost:5000/login")

    def test_login(self):
        driver = self.driver
        # Fill in username and password fields
        driver.find_element(By.NAME, "username").send_keys("john123")
        driver.find_element(By.NAME, "password").send_keys("Test@1234")
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

        # Wait for the next page to load
        time.sleep(2)
        
        # Assert that we landed on the dashboard page
        self.assertIn("dashboard", driver.current_url)

    def tearDown(self):
        # Close the browser
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()
