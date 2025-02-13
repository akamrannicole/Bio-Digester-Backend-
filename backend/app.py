from flask import Flask
from flask_cors import CORS
from app import create_app, db
from app.models import User, Product, Order, Receipt

app = create_app()
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5173"}})

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Product': Product, 'Order': Order, 'Receipt': Receipt}

if __name__ == '__main__':
    app.run(debug=True)

