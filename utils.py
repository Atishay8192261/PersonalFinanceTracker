import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objs as go
import json
from datetime import datetime, timedelta
from models import Transaction, db

def get_line_chart_data():
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        # Query daily expenses
        daily_expenses = db.session.query(
            Transaction.date,
            db.func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.type == 'expense',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.date).all()

        # Create line chart data
        dates = [start_date + timedelta(days=i) for i in range(31)]
        amounts = [0] * 31

        for expense in daily_expenses:
            index = (expense.date - start_date).days
            amounts[index] = expense.total

        # Create Plotly chart
        line_chart = go.Figure(data=go.Scatter(x=dates, y=amounts, mode='lines+markers'))
        line_chart.update_layout(
            title='Daily Expenses (Last 30 Days)',
            xaxis_title='Date',
            yaxis_title='Amount ($)',
            height=300,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        return json.dumps(line_chart, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        return None

def get_bar_chart_data(df):
    try:
        # Exclude goal-related transactions for visualizations
        df = df[df['type'].isin(['income', 'expense'])]
        fig = px.bar(df, x='category', y='amount', color='type', title='Income and Expenses by Category')
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        return None


def calculate_total_holdings():
    try:
        total_income = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(Transaction.type == 'income').scalar() or 0

        total_expense = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(Transaction.type == 'expense').scalar() or 0

        goal_allocations = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(Transaction.type == 'goal').scalar() or 0

        return total_income - (total_expense + abs(goal_allocations))
    except Exception as e:
        print(f"Error calculating total holdings: {e}")
        return 0
