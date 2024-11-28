from flask import Flask
from config import Config
from models import db, Budget
from routes import init_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Initialize budget if not exists
        if not Budget.query.first():
            initial_budget = Budget(amount=2000)
            db.session.add(initial_budget)
            db.session.commit()

    init_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)