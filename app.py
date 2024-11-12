from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import plotly.express as px
import plotly
import plotly.graph_objs as go
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
db = SQLAlchemy(app)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    recurring = db.Column(db.Boolean, default=False)

EXPENSE_CATEGORIES = [
    'Food & Dining', 'Transportation', 'Housing', 'Utilities', 'Healthcare',
    'Entertainment', 'Shopping', 'Personal', 'Education', 'Other'
]

INCOME_CATEGORIES = [
    'Salary', 'Investments', 'Freelance', 'Gifts', 'Refunds', 'Other'
]

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    transactions = Transaction.query.order_by(Transaction.date.desc()).limit(10).all()
    total_spent = sum(t.amount for t in Transaction.query.filter_by(type='expense').all())
    total_income = sum(t.amount for t in Transaction.query.filter_by(type='income').all())
    budget_goal = 1000  # Example monthly budget goal, you could make this dynamic

    # Prepare data for the line chart
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    daily_expenses = db.session.query(
        Transaction.date,
        db.func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.type == 'expense',
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).group_by(Transaction.date).all()

    dates = [start_date + timedelta(days=i) for i in range(31)]
    amounts = [0] * 31

    for expense in daily_expenses:
        index = (expense.date - start_date).days
        amounts[index] = expense.total

    line_chart = go.Figure(data=go.Scatter(x=dates, y=amounts, mode='lines+markers'))
    line_chart.update_layout(
        title='Daily Expenses (Last 30 Days)',
        xaxis_title='Date',
        yaxis_title='Amount ($)',
        height=300,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    line_chart_json = json.dumps(line_chart, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html', transactions=transactions, total_spent=total_spent, 
                           total_income=total_income, budget_goal=budget_goal, line_chart_json=line_chart_json)

@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        transaction = Transaction(
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            category=request.form['category'],
            amount=float(request.form['amount']),
            type=request.form['type']
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_transaction.html', expense_categories=EXPENSE_CATEGORIES, income_categories=INCOME_CATEGORIES)

@app.route('/get_categories/<transaction_type>')
def get_categories(transaction_type):
    if transaction_type == 'expense':
        return jsonify(EXPENSE_CATEGORIES)
    elif transaction_type == 'income':
        return jsonify(INCOME_CATEGORIES)
    else:
        return jsonify([])

@app.route('/visualize')
def visualize():
    transactions = Transaction.query.all()
    df = pd.DataFrame([{
        'date': t.date,
        'category': t.category,
        'amount': t.amount,
        'type': t.type
    } for t in transactions])

    if not df.empty:
        fig = px.bar(df, x='category', y='amount', color='type', title='Income and Expenses by Category')
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        graph_json = None
    return render_template('visualize.html', graph_json=graph_json)

@app.route('/reports')
def reports():
    transactions = Transaction.query.all()
    df = pd.DataFrame([{
        'category': t.category,
        'amount': t.amount,
        'type': t.type
    } for t in transactions])

    if not df.empty:
        monthly_summary = df.groupby(['type', 'category']).sum().reset_index()
        fig = px.bar(monthly_summary, x='category', y='amount', color='type', title='Monthly Spending Summary')
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        graph_json = None

    return render_template('reports.html', graph_json=graph_json)


if __name__ == '__main__':
    app.run(debug=True)