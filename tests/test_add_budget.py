from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
# Start the browser
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

# Step 1: Go to login page
driver.get("http://localhost:5000/login")

# Step 2: Fill and submit login form
driver.find_element(By.NAME, "username").send_keys("john123")
driver.find_element(By.NAME, "password").send_keys("Test@1234")
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

# Step 3: Wait and navigate to budget page
wait.until(EC.url_contains("/dashboard"))  # or homepage/dashboard after login
driver.get("http://localhost:5000/budget")

# Step 4: Fill out the budget form

# Select category (example: pick second option in dropdown)
category_select = Select(wait.until(EC.presence_of_element_located((By.NAME, "category_id"))))
category_select.select_by_index(1)  # Adjust if you want to match by text or value

# Enter target amount
driver.find_element(By.NAME, "target_amount").send_keys("5000")

# Select period
period_select = Select(driver.find_element(By.NAME, "period"))
period_select.select_by_value("monthly")

# Submit the form
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

# Step 5: Wait for success alert or confirmation
try:
    success_alert = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-success")))
    print("✅ Budget goal added successfully.")
except:
    print("❌ Failed to add budget goal.")
    driver.save_screenshot("budget_error.png")
time.sleep(5)

# Optional: Close the browser
# driver.quit()
