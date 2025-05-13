from locust import HttpUser, task, between

class FinanceAppUser(HttpUser):
    wait_time = between(1, 3)  # simulate user think time

    @task(1)
    def login(self):
        self.client.post("/login", data={
            "username": "john123",
            "password": "Test@1234"
        })

    @task(2)
    def view_dashboard(self):
        self.client.get("/dashboard")

    @task(3)
    def add_transaction(self):
        self.client.post("/transactions", data={
            "type": "expense",
            "amount": "500",
            "description": "groceries",
            "date": "2025-05-07",
            "payment_method": "cash",
            "category_id": "1"
        })
