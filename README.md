# 💸 Personal Finance Manager

A full-featured personal finance management web application built with **Flask**, **MySQL**, and **Jinja2** for server-side rendering. Users can track transactions, manage budgets, set savings goals, view AI-generated investment suggestions, and input transactions via voice—all from a single intuitive platform.

---

## 🧩 Features

- 🔐 User Registration & Authentication
- 💵 Income & Expense Tracking
- 📂 Category & Budget Management
- 🧾 Transaction History with Filters
- 🎯 Savings Goals Overview
- 📈 AI Investment Suggestions (Gemini API)
- 🎤 Voice-based Transaction Input
- 🧑 User Profile Page
- 📊 Interactive Charts (Chart.js)

---

## 🛠 Tech Stack

- **Frontend**: HTML, CSS, JavaScript (Jinja templates)
- **Backend**: Python, Flask
- **Database**: MySQL
- **AI Integration**: Gemini API (via `gemini_helper.py`)
- **Voice Input**: Web Speech API
- **Charting**: Chart.js

---

Pre-requisites

    • Python 3.x installed
    • MySQL installed

Backend Setup

    1. Clone the repository.
    2. Install required dependencies:

pip install -r requirements.txt

    3. Configure the .env file with the following:

SECRET_KEY=<your-secret-key> 
DATABASE_USER=<your-database-username> 
DATABASE_PASSWORD=<your-database-password> 
DATABASE_NAME=<database-name>
    4. Run the Flask application:	

python app.py
