from flask import render_template, request, redirect, url_for, flash, jsonify
from models import Transaction, Budget, Goal, db
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from utils import get_line_chart_data, get_bar_chart_data, calculate_total_holdings
from datetime import datetime, date
import pandas as pd
import calendar

def init_routes(app):

    @app.route('/')
    def index():

        """Render the dashboard with financial summaries and charts."""

        current_date = date.today()

        #Getting the first and last day of the current month
        first_day_of_month = date(current_date.year, current_date.month, 1)
        last_day_of_month = date(
            current_date.year,
            current_date.month,
            calendar.monthrange(current_date.year, current_date.month)[1]
        )

        #Fetching the latest 10 transactions
        transactions = Transaction.query.order_by(Transaction.date.desc()).limit(10).all()

        #Calculating total income and expenses for the current month
        total_income = sum(t.amount for t in Transaction.query.filter(
            Transaction.type == 'income',
            Transaction.date.between(first_day_of_month, last_day_of_month)
        ).all())

        total_expense = sum(t.amount for t in Transaction.query.filter(
            Transaction.type == 'expense',
            Transaction.date.between(first_day_of_month, last_day_of_month)
        ).all())

        #calculating total savings for the current month
        total_savings = total_income - total_expense

        #calculating total holdings
        total_holdings = calculate_total_holdings()

        #Fetching the budget goal or setting a default
        budget = Budget.query.first()
        budget_goal = budget.amount if budget else 1000  # Default is $1000

        #generating the line chart data
        line_chart_json = get_line_chart_data()

        #rendering the  index template with the data
        return render_template(
            'index.html',
            transactions=transactions,
            total_spent=total_expense,
            total_savings=total_savings,
            total_holdings=total_holdings,
            budget_goal=budget_goal,
            line_chart_json=line_chart_json
        )

    @app.route('/transactions')
    def transactions():
        """Display all transactions."""
        all_transactions = Transaction.query.order_by(Transaction.date.desc()).all()

        return render_template('transactions.html', transactions=all_transactions)

    @app.route('/add_transaction', methods=['GET', 'POST'])
    def add_transaction():
        """Add a new transaction."""
        if request.method == 'POST':
            try:

                #trying to parse the transaction date
                transaction_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
                current_date = date.today()

                #c=hecking if the transaction is valid for the current month or is it income
                if (transaction_date.year == current_date.year and transaction_date.month == current_date.month) or request.form['type'] == 'income':
                    # Creating a new transaction object
                    transaction = Transaction(
                        date=transaction_date,
                        category=request.form['category'],
                        amount=float(request.form['amount']),
                        type=request.form['type']
                    )
                    db.session.add(transaction)

                    #Adjusting the budget if it's an expense in the current month
                    if transaction.type == 'expense' and transaction_date.month == current_date.month:
                        budget = Budget.query.first()
                        if budget:
                            budget.amount -= transaction.amount

                    db.session.commit()
                    flash('Transaction added successfully!', 'success')

                else:
                    flash('Only income transactions can be added for previous months.', 'warning')

            except Exception as e:
                db.session.rollback()
                flash(f"Error adding transaction: {str(e)}", 'danger')

            return redirect(url_for('transactions'))

        #Rendering the add transaction form
        return render_template(
            'add_transaction.html',
            expense_categories=EXPENSE_CATEGORIES,
            income_categories=INCOME_CATEGORIES
        )

    @app.route('/get_categories/<transaction_type>')
    def get_categories(transaction_type):

        """Return categories based on transaction type."""

        if transaction_type == 'expense':
            return jsonify(EXPENSE_CATEGORIES)
        
        elif transaction_type == 'income':
            return jsonify(INCOME_CATEGORIES)
        
        else:
            #returns an empty list for invalid types
            return jsonify([])

    @app.route('/reports')
    def reports():

        """Generate and display financial reports."""

        #Fetching income and expense transactions
        transactions = Transaction.query.filter(Transaction.type.in_(['income', 'expense'])).all()

        #Creating a DataFrame from transactions
        df = pd.DataFrame([{
            'category': t.category,
            'amount': t.amount,
            'type': t.type
        } for t in transactions])

        #Generrating the bar chart data if the DataFrame is not empty
        if not df.empty:
            monthly_summary = df.groupby(['type', 'category']).sum().reset_index()
            graph_json = get_bar_chart_data(monthly_summary)
        
        else:
            graph_json = None

        #Rendering the reports template
        return render_template('reports.html', graph_json=graph_json)

    @app.route('/update_budget', methods=['POST'])
    def update_budget():

        """Update the user's budget goal."""

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

        """Display and add financial goals."""

        if request.method == 'POST':
            try:
                #creating a new goal
                goal = Goal(
                    name=request.form['name'],
                    target_amount=float(request.form['target_amount']),
                    deadline=datetime.strptime(request.form['deadline'], '%Y-%m-%d').date()
                )
                db.session.add(goal)
                db.session.commit()
                flash('Goal added successfully!', 'success')

            except Exception as e:
                db.session.rollback()
                flash(f"Error adding goal: {str(e)}", 'danger')

        #Fetching the goals
        goals = Goal.query.all()
        
        return render_template('goals.html', goals=goals)

    @app.route('/allocate_funds/<int:goal_id>', methods=['POST'])
    def allocate_funds(goal_id):

        """Allocate funds to a specific goal."""

        try:
            goal = Goal.query.get(goal_id)
            amount = float(request.form['amount'])
            total_holdings = calculate_total_holdings()

            #Checking if there are sufficient funds
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

        """Delete a goal and refund allocated funds."""

        try:
            goal = Goal.query.get(goal_id)
            if goal:
                goal.refund_allocation()  #Refunds funds before deletion
                db.session.delete(goal)
                db.session.commit()
                flash(f"Goal '{goal.name}' deleted successfully!", 'success')

            else:
                flash("Goal not found!", 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting goal: {str(e)}", 'danger')
            
        return redirect(url_for('goals'))
