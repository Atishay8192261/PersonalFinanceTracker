import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objs as go
import json
from datetime import datetime, timedelta
from models import Transaction, db

def get_line_chart_data():

    """Generates JSON data for the daily expenses line chart."""

    try:

        #Setting the date range for the last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        #Querying daily expenses from the database
        daily_expenses = db.session.query(
            Transaction.date,
            db.func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.type == 'expense',
            Transaction.date.between(start_date, end_date)
        ).group_by(Transaction.date).all()

        #Preparing dates and amounts lists for the chart
        dates = [start_date + timedelta(days=i) for i in range(31)]
        amounts = [0] * 31

        #Filling amounts with the total expenses for each date
        for expense in daily_expenses:
            index = (expense.date - start_date).days
            amounts[index] = expense.total

        #Creating the line chart using Plotly
        line_chart = go.Figure(
            data=go.Scatter(x=dates, y=amounts, mode='lines+markers')
        )

        line_chart.update_layout(
            title='Daily Expenses (Last 30 Days)',
            xaxis_title='Date',
            yaxis_title='Amount ($)',
            height=300,
            margin=dict(l=0, r=0, t=30, b=0)
        )

        #Converting the chart to JSON format
        return json.dumps(line_chart, cls=plotly.utils.PlotlyJSONEncoder)
    
    except Exception as e:

        #Returning None if an error occurs
        return None

def get_bar_chart_data(df):

    """Generates JSON data for the income and expenses bar chart by category."""

    try:

        #Filtering out goal-related transactions
        df = df[df['type'].isin(['income', 'expense'])]

        #Creating the bar chart using Plotly Express
        fig = px.bar(
            df,
            x='category',
            y='amount',
            color='type',
            title='Income and Expenses by Category'
        )

        #Converting the chart to JSON format
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    except Exception as e:

        #Returning None if an error occurs
        return None

def calculate_total_holdings():
    """Calculate the net total holdings."""
    try:
        #Summing up all income amounts
        total_income = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(Transaction.type == 'income').scalar() or 0

        #Summing up all expense amounts
        total_expense = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(Transaction.type == 'expense').scalar() or 0

        #Summing up all goal allocated amounts
        goal_allocations = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(Transaction.type == 'goal').scalar() or 0

        #Calculating the  total holdings
        total_holdings = total_income - (total_expense + abs(goal_allocations))
        return total_holdings
    except Exception as e:
        print(f"Error calculating total holdings: {e}")
        #Returning zero if an error occurs
        return 0
