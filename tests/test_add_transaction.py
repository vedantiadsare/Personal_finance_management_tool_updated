from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time


BASE_URL = "http://localhost:5000"
EMAIL = "john123"
PASSWORD = "Test@1234"

def test_add_transaction():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    
    try:
        print("🚀 Navigating to login page...")
        driver.get(f"{BASE_URL}/login")

        print("🔐 Filling login form...")
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_input = driver.find_element(By.NAME, "password")
        login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        email_input.send_keys(EMAIL)
        password_input.send_keys(PASSWORD)
        login_btn.click()

        print("✅ Logged in. Navigating to /transactions...")
        wait.until(EC.url_contains("/dashboard"))
        driver.get(f"{BASE_URL}/transactions")

        print("➕ Clicking Add Transaction button...")
        add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-bs-target='#transactionModal']")))
        add_btn.click()

        print("📋 Filling transaction form...")
        wait.until(EC.visibility_of_element_located((By.ID, "transactionModal")))

        Select(driver.find_element(By.ID, "transaction_type")).select_by_value("income")
        driver.find_element(By.ID, "amount").send_keys("5000")
        driver.find_element(By.ID, "description").send_keys("Test  Income")

        # Set a valid date using JavaScript to avoid browser issues with HTML5 date pickers
        # Locate the transaction form (adjust selector as per your HTML)
        form = driver.find_element(By.ID, "transactionForm")  # or By.CLASS_NAME / By.TAG_NAME / other if needed

        # Now safely access the date input inside the form
        date_input = form.find_element(By.NAME, "date")

        # Set the date using JavaScript
        driver.execute_script("arguments[0].value = arguments[1];", date_input, "2025-05-05")



        Select(driver.find_element(By.ID, "payment_method")).select_by_value("Cash")

        category_select = Select(driver.find_element(By.ID, "category_id"))
        for option in category_select.options:
            if option.get_attribute("data-type") == "income":
                category_select.select_by_value(option.get_attribute("value"))
                break

        driver.find_element(By.CSS_SELECTOR, "#transactionForm button[type='submit']").click()

        print("⏳ Waiting for success alert...")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-success")))
        print("✅ Transaction added successfully.")

    except Exception as e:
        print("❌ Test failed:", e)
        driver.save_screenshot("error_screenshot.png")
        print("📸 Screenshot saved as error_screenshot.png")
    finally:
        time.sleep(3)
        driver.quit()

if __name__ == "__main__":
    test_add_transaction()
