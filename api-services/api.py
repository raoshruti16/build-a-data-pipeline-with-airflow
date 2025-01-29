from flask import Flask, jsonify, request
import csv
from datetime import datetime

DATA_DIR = './data'

app = Flask(__name__)

# Load data from CSV files
def load_data(file_path, key):
    data = {}
    with open(file_path, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            data[row[key]] = row
    return data

customers = load_data(f'{DATA_DIR}/customers.csv', 'customer_id')
orders = load_data(f'{DATA_DIR}/orders.csv', 'order_id')
products = load_data(f'{DATA_DIR}/products.csv', 'product_id')

# Convert order product_quantities from string to dictionary
for order_id, order in orders.items():
    order['product_quantities'] = eval(order['product_quantities'])

@app.route('/api/customers', methods=['GET'])
def get_customers():
    return jsonify(list(customers.values()))

@app.route('/api/customers/<customer_id>', methods=['GET'])
def get_customer_by_id(customer_id):
    customer = customers.get(customer_id)
    if customer:
        return jsonify(customer)
    else:
        return jsonify({'error': 'Customer not found'}), 404

@app.route('/api/orders', methods=['GET'])
def get_orders():
    order_date = request.args.get('order_date')
    if order_date:
        filtered_orders = [
            order for order in orders.values()
            if order['order_date'] == order_date
        ]
        return jsonify(filtered_orders)
    return jsonify(list(orders.values()))

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order_by_id(order_id):
    order = orders.get(order_id)
    if order:
        return jsonify(order)
    else:
        return jsonify({'error': 'Order not found'}), 404

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(list(products.values()))

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product_by_id(product_id):
    product = products.get(product_id)
    if product:
        return jsonify(product)
    else:
        return jsonify({'error': 'Product not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
