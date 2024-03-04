from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock.db'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'purchase' or 'sale'
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    product = db.relationship('Product', backref=db.backref('transactions', lazy=True))

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html',products=products)

@app.route('/add', methods=['POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        
        product = Product(name=name, quantity=quantity, price=price)
        db.session.add(product)
        db.session.commit()
    return redirect("/")

@app.route('/transaction', methods=['POST'])
def add_transaction():
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        transaction_type = request.form['transaction_type']
        quantity = int(request.form['quantity'])

        product = Product.query.get(product_id)
        if product is None:
            return f"Product with ID {product_id} not found"

        if transaction_type == 'purchase':
            product.quantity += quantity
        elif transaction_type == 'sale':
            if product.quantity >= quantity:
                product.quantity -= quantity
            else:
                return "Insufficient stock for sale"

        transaction = Transaction(product_id=product.id, transaction_type=transaction_type, quantity=quantity)
        db.session.add(transaction)
        db.session.commit()

    return redirect(url_for('index'))


@app.route('/transaction_history')
def transaction_history():
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('transaction_history.html', transactions=transactions)

@app.route('/products')
def products_table():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route("/delete/<int:id>")
def delete(id):
    product = Product.query.filter_by(id=id).first()
    db.session.delete(product)
    db.session.commit()
    return redirect("/products")

@app.route("/delete_transaction/<int:id>")
def delete_transaction(id):
    transaction = Transaction.query.filter_by(id=id).first()
    db.session.delete(transaction)
    db.session.commit()
    return redirect("/transaction_history")

@app.route('/get_product_id')
def get_product_id():
    product_name = request.args.get('product_name')
    product = Product.query.filter_by(name=product_name).first()
    
    if product:
        return jsonify({'product_id': product.id})
    else:
        return jsonify({'error': 'Product not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
