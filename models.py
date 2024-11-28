from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Transaction(db.Model):

    """Model for transactions like income, expenses, and goal allocations."""

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

    """Model for the user's budget goal."""

    __tablename__ = 'budget'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Budget {self.amount}>"

class Goal(db.Model):

    """Model for financial goals."""

    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0, nullable=False)
    deadline = db.Column(db.Date, nullable=False)

    def allocate_funds(self, amount):

        """Allocate funds to the goal and deduct from holdings."""

        if amount > 0:
            self.current_amount += amount
            transaction = Transaction(
                date=datetime.now(),
                category=f"Goal Allocation: {self.name}",
                amount=-amount, #deducts from holdings
                type="goal"  #marked as a goal transaction
            )
            db.session.add(transaction)
            db.session.commit()

    def refund_allocation(self):

        """Refund allocated funds back to holdings before deletion."""

        if self.current_amount > 0:
            transaction = Transaction(
                date=datetime.now(),
                category=f"Goal Refund: {self.name}",
                amount=self.current_amount,
                type="goal"  #marked as a goal transaction
            )
            db.session.add(transaction)
            self.current_amount = 0
            db.session.commit()
