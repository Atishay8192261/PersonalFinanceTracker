from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db = SQLAlchemy()
Base = declarative_base()

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    recurring = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Transaction {self.id} {self.date} {self.category} {self.amount} {self.type}>"

class Budget(db.Model):
    __tablename__ = 'budget'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Budget {self.amount}>"