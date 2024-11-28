from flask import render_template, request, redirect, url_for, flash, jsonify
from models import Transaction, Budget, db
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from utils import get_line_chart_data, get_bar_chart_data
from datetime import datetime, date
import pandas as pd
import calendar

def init_routes(app):
    @app.route('/')
    def index():
        current_date = date.today()
        first_day_of_month = date(current_date.year, current_date.month, 1)
        last_day_of_month = date(current_date.year, current_date.month, calendar.monthrange(current_date.year, current_date.month)[1])

        transactions = Transaction.query.order_by(Transaction.date.desc()).limit(10).all()
        total_spent = sum(t.amount for t in Transaction.query.filter(Transaction.type == 'expense', Transaction.date >= first_day_of_month, Transaction.date <= last_day_of_month).all())
        total_income = sum(t.amount for t in Transaction.query.filter(Transaction.type == 'income', Transaction.date >= first_day_of_month, Transaction.date <= last_day_of_month).all())
        total_holdings = sum(t.amount for t in Transaction.query.filter(Transaction.type == 'income').all()) - sum(t.amount for t in Transaction.query.filter(Transaction.type == 'expense').all())
        
        budget = Budget.query.first()
        budget_goal = budget.amount if budget else 2000  # Default to 2000 if no budget is set

        line_chart_json = get_line_chart_data()
        return render_template('index.html', transactions=transactions, total_spent=total_spent, 
                               total_income=total_income, total_holdings=total_holdings,
                               budget_goal=budget_goal, line_chart_json=line_chart_json)

    @app.route('/add_transaction', methods=['GET', 'POST'])
    def add_transaction():
        if request.method == 'POST':
            try:
                transaction_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
                current_date = date.today()
                
                if transaction_date.year == current_date.year and transaction_date.month == current_date.month:
                    transaction = Transaction(
                        date=transaction_date,
                        category=request.form['category'],
                        amount=float(request.form['amount']),
                        type=request.form['type']
                    )
                    db.session.add(transaction)
                    db.session.commit()
                    flash('Transaction added successfully!', 'success')
                else:
                    flash('Transactions can only be added for the current month.', 'warning')
            except Exception as e:
                flash(f"Error adding transaction: {str(e)}", 'danger')
            return redirect(url_for('index'))
        return render_template('add_transaction.html', expense_categories=EXPENSE_CATEGORIES, income_categories=INCOME_CATEGORIES)

    @app.route('/get_categories/<transaction_type>')
    def get_categories(transaction_type):
        if transaction_type == 'expense':
            return jsonify(EXPENSE_CATEGORIES)
        elif transaction_type == 'income':
            return jsonify(INCOME_CATEGORIES)
        else:
            return jsonify([])  # Return an empty list for invalid transaction types

    @app.route('/visualize')
    def visualize():
        transactions = Transaction.query.all()
        df = pd.DataFrame([{
            'date': t.date,
            'category': t.category,
            'amount': t.amount,
            'type': t.type
        } for t in transactions])

        graph_json = get_bar_chart_data(df) if not df.empty else None
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
            graph_json = get_bar_chart_data(monthly_summary)
        else:
            graph_json = None

        return render_template('reports.html', graph_json=graph_json)

    @app.route('/update_budget', methods=['POST'])
    def update_budget():
        try:
            new_budget = float(request.form['budget'])
            budget = Budget.query.first()
            if budget:
                budget.amount = new_budget
            else:
                budget = Budget(amount=new_budget)
                db.session.add(budget)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Budget updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})
