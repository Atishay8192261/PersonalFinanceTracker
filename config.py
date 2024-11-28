import os
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from a .env file

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_default_secret_key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///finance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

EXPENSE_CATEGORIES = [
    'Food & Dining', 'Transportation', 'Housing', 'Utilities', 'Healthcare',
    'Entertainment', 'Shopping', 'Personal', 'Education', 'Other'
]

INCOME_CATEGORIES = [
    'Salary', 'Investments', 'Freelance', 'Gifts', 'Refunds', 'Other'
]
