import pandas as pd
import requests
import os
import json
from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Table, MetaData, and_, Column, String, Integer, Float, Date

API_URL = 'http://api-services:5000/api'
AIRFLOW_DATA_DIR = '/opt/airflow/data'
DATA_DIR = f'{AIRFLOW_DATA_DIR}/order_analysis'
DATABASE_FILE = f'{AIRFLOW_DATA_DIR}/api_database.db'

@dag(
    description='ETL pipeline for order analysis.' +
                'Extracts data from the microservices API and loads it into a SQLite database.',
    schedule='@daily',
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'start_date': datetime(2024, 6, 17),
        'retries': 10,
        'retry_delay': timedelta(minutes=1),
    }
)
def order_analysis_dag():

    @task(provide_context=True)
    def extract(**kwargs):
        """Extract data from the API into CSV files"""

        # Use the execution date to get orders for the current date
        date = kwargs["logical_date"].strftime("%Y-%m-%d")

        # Skip this task if the files exist
        for file in ['customers', 'orders', 'products']:
            if os.path.exists(f'{DATA_DIR}/{file}-{date}.csv'):
                print(f'{DATA_DIR}/{file}-{date}.csv already exists, skipping extract task')
                return

        # Extract data from the API
        customers = requests.get(f'{API_URL}/customers').json()
        orders = requests.get(f'{API_URL}/orders?order_date={date}').json()
        products = requests.get(f'{API_URL}/products').json()

        # Save data to CSV files
        os.makedirs(DATA_DIR, exist_ok=True)
        pd.DataFrame(customers).to_csv(f'{DATA_DIR}/customers-{date}.csv', index=False)
        pd.DataFrame(orders).to_csv(f'{DATA_DIR}/orders-{date}.csv', index=False)
        pd.DataFrame(products).to_csv(f'{DATA_DIR}/products-{date}.csv', index=False)

    @task(provide_context=True)
    def transform(**kwargs):
        """Join the data from the CSV files"""

        # Use the execution date to get orders for the current date
        date = kwargs["logical_date"].strftime("%Y-%m-%d")

        # Skip this task if there are no files or they're empty
        for file in ['customers', 'orders', 'products']:
            if (
                not os.path.exists(f'{DATA_DIR}/{file}-{date}.csv')
                or os.path.getsize(f'{DATA_DIR}/{file}-{date}.csv') == 0
            ):
                print(f'{DATA_DIR}/{file}-{date}.csv does not exist or is empty, skipping transform task')
                raise AirflowSkipException

        try:
            customers = pd.read_csv(f'{DATA_DIR}/customers-{date}.csv')
            orders = pd.read_csv(f'{DATA_DIR}/orders-{date}.csv')
            products = pd.read_csv(f'{DATA_DIR}/products-{date}.csv')
        except pd.errors.EmptyDataError as e:
            print(f'{e}, skipping transform task')
            raise AirflowSkipException


        # Normalize the product quantities from a list of {ID:quantity} dictionaries to separate rows
        normalized_orders = pd.concat(
            orders.apply(normalize_product_quantities, axis=1).values
        )

        normalized_orders.drop(columns=['product_quantities'], inplace=True)

        # Join the data
        transformed_data = pd.merge(
            pd.merge(normalized_orders, customers, on='customer_id', how='left'),
            products, on='product_id', how='left'
        )

        # Save the transformed data to a CSV file
        transformed_data.to_csv(f'{DATA_DIR}/transformed_data-{date}.csv', index=False)

    @task(provide_context=True)
    def load(**kwargs):
        """Load the transformed data into a SQLite database"""
        
        # Use the execution date to get orders for the current date
        date = kwargs["logical_date"].strftime("%Y-%m-%d")

        # Skip this task if the file is empty
        if (
            not os.path.exists(f'{DATA_DIR}/transformed_data-{date}.csv')
            or os.path.getsize(f'{DATA_DIR}/transformed_data-{date}.csv') == 0
        ):
            print(f'{DATA_DIR}/transformed_data-{date}.csv does not exist or is empty, skipping load task')
            raise AirflowSkipException
        
        transformed_data = pd.read_csv(f'{DATA_DIR}/transformed_data-{date}.csv')
        transformed_data['order_date'] = pd.to_datetime(date)

        conn, final_data_table = setup_database_connection()

        upsert(conn, final_data_table, transformed_data)

        conn.close()

        rows_inserted = len(transformed_data)
        print(f'{rows_inserted} rows inserted into final_data table')

    extract() >> transform() >> load()

order_analysis_dag()

def normalize_product_quantities(row):
    product_quantities = json.loads(row['product_quantities'].replace("'", '"'))
    normalized_rows = []
    for product_id, quantity in product_quantities.items():
        normalized_row = row.copy()
        normalized_row['product_id'] = product_id
        normalized_row['quantity'] = quantity
        normalized_rows.append(normalized_row)
    return pd.DataFrame(normalized_rows)


def setup_database_connection():
    engine = create_engine(f'sqlite:///{DATABASE_FILE}')
    conn = engine.connect()
    metadata = MetaData(bind=engine)

    final_data_table = Table('final_data', metadata,
        Column('order_id', String, primary_key=True),
        Column('customer_id', String, primary_key=True),
        Column('product_id', String, primary_key=True),
        Column('product_name', String),
        Column('product_description', String),
        Column('product_price', Float),
        Column('quantity', Integer),
        Column('order_date', Date),
        Column('order_total', Float),
        Column('first_name', String),
        Column('last_name', String),
        Column('email', String),
        Column('address', String),
        Column('phone_number', String),
        Column('state', String),
        Column('city', String),
        Column('zip_code', String),
        extend_existing=True,
    )

    # Create the table if it doesn't exist
    metadata.create_all(engine)
    final_data_table = Table('final_data', metadata, autoload_with=engine)

    return conn, final_data_table
    

def upsert(conn, table, data):
    for _index, row in data.iterrows():
        # Try to fetch existing row
        stmt = table.select().where(
            and_(
                table.c.order_id == row['order_id'],
                table.c.customer_id == row['customer_id'],
                table.c.product_id == row['product_id']
            )
        )
        result = conn.execute(stmt).fetchone()

        if result:
            # Update existing row
            stmt = table.update().where(
                and_(
                    table.c.order_id == row['order_id'],
                    table.c.customer_id == row['customer_id'],
                    table.c.product_id == row['product_id']
                )
            ).values(row.to_dict())
        else:
            # Insert new row
            stmt = table.insert().values(row.to_dict())

        conn.execute(stmt)