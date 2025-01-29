"""
This file uses Faker to generate datasets for the project.

The datasets generated are:
1. Customers: customer_id, first_name, last_name, email, phone_number, address, city, state, zip_code
2. Orders: order_id, customer_id, products, order_date, order_total
3. Products: product_id, product_name, product_description, product_price

For orders, products contains a list of product_id and quantity. The order_total is the sum of the product prices.

The datasets are saved as CSV files in the current directory.
"""

import random
from typing import List
from faker import Faker
from faker.providers import BaseProvider
import pandas as pd

OUTPUT_DIR = './api-services/data'

class ProductProvider(BaseProvider):
    def random_company_product(self):
        products = [
            "Laptop", "Smartphone", "Tablet", "Headphones", "Smartwatch", 
            "Camera", "Printer", "Monitor", "Keyboard", "Mouse"
        ]
        return random.choice(products)

fake = Faker()
fake.add_provider(ProductProvider)

def generate_customers(n):
    customers = []
    for _ in range(n):
        customer = {
            'customer_id': fake.uuid4(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'phone_number': fake.phone_number(),
            'address': fake.street_address(),
            'city': fake.city(),
            'state': fake.state_abbr(),
            'zip_code': fake.zipcode(),
        }
        customers.append(customer)
    return customers

def generate_products(n):
    products = []
    for _ in range(n):
        product = {
            'product_id': fake.uuid4(),
            # Generate more realistic product names
            'product_name': f"{fake.bs().split()[1].capitalize()} {fake.bs().split()[0].capitalize()} {fake.random_company_product()}",
            'product_description': fake.sentence(),
            'product_price': f"{random.randint(10, 1000)}.{random.randint(0, 99)}",
        }
        products.append(product)
    return products

def generate_orders(customers, products, n):
    orders = []
    for _ in range(n):
        chosen_products = random.sample(products, k=random.randint(1, 5))
        order = {
            'order_id': fake.uuid4(),
            'customer_id': random.choice(customers)['customer_id'],
            'product_quantities': {product['product_id']: random.randint(1, 5) for product in chosen_products},
            'order_date': fake.date_time_between(start_date="-15d", end_date="now").strftime('%Y-%m-%d'),
        }
        order['order_total'] = sum_prices(chosen_products, order['product_quantities'])
        orders.append(order)
    return orders

def sum_prices(products: list, product_quantities: dict) -> str:
    """Adds prices represented as floats by using minor units (cents) and integer quantities."""
    assert len(products) == len(product_quantities)
    total = 0
    for product in products:
        major, minor = product['product_price'].split('.')
        price = int(major) * 100 + int(minor)
        total += price * product_quantities[product['product_id']]
    return f"{total // 100}.{total % 100}"


def main():

    customers = generate_customers(100)
    products = generate_products(10)
    orders = generate_orders(customers, products, 100)

    customers_df = pd.DataFrame(customers)
    customers_df.to_csv(f'{OUTPUT_DIR}/customers.csv', index=False)

    products_df = pd.DataFrame(products)
    products_df.to_csv(f'{OUTPUT_DIR}/products.csv', index=False)

    orders_df = pd.DataFrame(orders)
    orders_df.to_csv(f'{OUTPUT_DIR}/orders.csv', index=False)


if __name__ == '__main__':
    main()