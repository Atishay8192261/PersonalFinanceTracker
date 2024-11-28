from flask import render_template, request, redirect, url_for, flash, jsonify
from models import Transaction, Budget, Goal, db
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from utils import get_line_chart_data, get_bar_chart_data, calculate_total_holdings
from datetime import datetime, date
import pandas as pd
import calendar

def init_routes(app):
    @app.route('/')
    @app.route('/')
    def index():
        current_date = date.today()
        first_day_of_month = date(current_date.year, current_date.month, 1)
        last_day_of_month = date(current_date.year, current_date.month, calendar.monthrange(current_date.year, current_date.month)[1])

        transactions = Transaction.query.order_by(Transaction.date.desc()).limit(10).all()

        # Calculate Total Savings (current month income - current month expenses)
        total_income = sum(t.amount for t in Transaction.query.filter(
            Transaction.type == 'income',
            Transaction.date >= first_day_of_month,
            Transaction.date <= last_day_of_month
        ).all())
        total_expense = sum(t.amount for t in Transaction.query.filter(
            Transaction.type == 'expense',
            Transaction.date >= first_day_of_month,
            Transaction.date <= last_day_of_month
        ).all())
        total_savings = total_income - total_expense

        total_holdings = calculate_total_holdings()  # Holdings remain unchanged
        budget = Budget.query.first()
        budget_goal = budget.amount if budget else 1000  # Default budget goal

        line_chart_json = get_line_chart_data()
        return render_template('index.html', transactions=transactions, total_spent=total_expense,
                            total_savings=total_savings, total_holdings=total_holdings,
                            budget_goal=budget_goal, line_chart_json=line_chart_json)


    @app.route('/transactions')
    def transactions():
        all_transactions = Transaction.query.order_by(Transaction.date.desc()).all()
        return render_template('transactions.html', transactions=all_transactions)

    @app.route('/add_transaction', methods=['GET', 'POST'])
    def add_transaction():
        if request.method == 'POST':
            try:
                transaction_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
                current_date = date.today()

                if (transaction_date.year == current_date.year and transaction_date.month == current_date.month) or request.form['type'] == 'income':
                    transaction = Transaction(
                        date=transaction_date,
                        category=request.form['category'],
                        amount=float(request.form['amount']),
                        type=request.form['type']
                    )
                    db.session.add(transaction)

                    if transaction.type == 'expense' and transaction_date.month == current_date.month:
                        # Adjust savings for current month expenses
                        budget = Budget.query.first()
                        if budget:
                            budget.amount -= transaction.amount

                    db.session.commit()
                    flash('Transaction added successfully!', 'success')
                else:
                    flash('Only income transactions can be added for previous months.', 'warning')
            except Exception as e:
                flash(f"Error adding transaction: {str(e)}", 'danger')
            return redirect(url_for('transactions'))
        return render_template('add_transaction.html', expense_categories=EXPENSE_CATEGORIES, income_categories=INCOME_CATEGORIES)


    @app.route('/get_categories/<transaction_type>')
    def get_categories(transaction_type):
        if transaction_type == 'expense':
            return jsonify(EXPENSE_CATEGORIES)
        elif transaction_type == 'income':
            return jsonify(INCOME_CATEGORIES)
        else:
            return jsonify([])  # Return an empty list for invalid transaction types

    @app.route('/reports')
    def reports():
        # Only include income and expense transactions
        transactions = Transaction.query.filter(Transaction.type.in_(['income', 'expense'])).all()
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

    @app.route('/goals', methods=['GET', 'POST'])
    def goals():
        if request.method == 'POST':
            try:
                goal_name = request.form['name']
                target_amount = float(request.form['target_amount'])
                deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d').date()
                goal = Goal(name=goal_name, target_amount=target_amount, current_amount=0, deadline=deadline)
                db.session.add(goal)
                db.session.commit()
                flash('Goal added successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding goal: {str(e)}", 'danger')
        goals = Goal.query.all()
        return render_template('goals.html', goals=goals)
    
    
    @app.route('/allocate_funds/<int:goal_id>', methods=['POST'])
    def allocate_funds(goal_id):
        try:
            goal = Goal.query.get(goal_id)
            amount = float(request.form['amount'])
            total_holdings = calculate_total_holdings()

            if amount > total_holdings:
                flash("Insufficient funds to allocate.", 'danger')
            elif goal:
                goal.allocate_funds(amount)
                flash(f"Funds allocated to '{goal.name}' successfully!", 'success')
            else:
                flash("Goal not found!", 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f"Error allocating funds: {str(e)}", 'danger')
        return redirect(url_for('goals'))


    @app.route('/delete_goal/<int:goal_id>', methods=['POST'])
    def delete_goal(goal_id):
        try:
            goal = Goal.query.get(goal_id)
            if goal:
                goal.refund_allocation()  # Refund any allocated funds before deletion
                db.session.delete(goal)
                db.session.commit()
                flash(f"Goal '{goal.name}' deleted successfully!", 'success')
            else:
                flash("Goal not found!", 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting goal: {str(e)}", 'danger')
        return redirect(url_for('goals'))
