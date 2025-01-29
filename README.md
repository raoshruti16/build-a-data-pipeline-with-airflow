# Airflow demo course

## 1. Development environment (optional)

To be able to develop and change the code, you have 2 options: you can run this locally or in a development container. Both options are described below. 

### 1.1 Option 1: Running locally

To run this locally, you'll need to install the following:
- [Python 3.6+](https://www.python.org/downloads/) - **I recommend using [pyenv](https://github.com/pyenv/pyenv) to install it, and use the version in the [`.python-version`](./.python-version) file**
- [Docker](https://www.docker.com/products/docker-desktop)

Once you have these installed, you can run the following commands to get started:

### 1.2 Option 2: Running in a development container

This repo uses DevContainers to provide a consistent development environment.
This is so that you have the required dependencies (such as airflow libraries and python)
when running and debugging the code. But to run the whole stack we use docker-compose.


To get started, you'll need to install the following:
- [Docker](https://www.docker.com/products/docker-desktop)
- [Visual Studio Code](https://code.visualstudio.com/)
- [Remote Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

Once you have these installed, you can open this repo in VS Code and click the "Reopen in Container" button that appears in the bottom right corner of the window.

## 2. Installing dependencies

No matter which option you choose, you'll need to install the dependencies. It's recommended to use a virtual environment. You can do this by running the following command (run it inside the devcontainer if you're using that):

```bash
python -m virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

Alternatively, all these commands can be executed by running the script:
```bash
./1-install.sh
```

## 3. Generating API data

The data in [`api-services/data`](./api-services/data) is generated using the [`generate-datasets.py`](./generate-datasets.py) script. If you want to generate new data (so that the dates are current for the orders data), you can run this script.

```bash
source env/bin/activate
python generate-datasets.py
```

Alternatively, all these commands can be executed by running the script:
```bash
./2-generate-datasets.sh
```

## 3.1 Updating the airflow DAG to start on a recent date

Currently, the DAG is set to start on 2024-06-17. If you want to change this date, you can update the `start_date` parameter inside the `@dag` decorator in the [`order_analysis_dag.py`](./dags/order_analysis_dag.py) file.
Use a date about a week before the current date to make sure you have data to process.

```python
'start_date': datetime(2024, 6, 17),
```


## 4. Initializing airflow

All the commands in this section can be executed by running the script:
```bash
./3-init.sh
```
But if you prefer to run each command manually, keep reading this section.

We run airflow as a stack in docker compose. Run these commands outside the devcontainer.

You'll need some folders to store the logs and the DAGs. You can create these with:

```bash
mkdir -p ./dags ./logs ./data
```

The first time you run a new stack you'll need to initialize the database and create a user.

```bash
docker-compose run --rm webserver airflow db init
docker-compose run --rm webserver airflow users create \
    --username admin \
    --firstname admin \
    --lastname admin \
    --role Admin \
    --password admin \
    --email admin@example.com
```

After that's done, you can start the stack with:

```bash
docker-compose up --build -d
```
## 5. Accessing the UI

You can access the airflow UI at [http://localhost:8080](http://localhost:8080)

## 6. Running the example

To run the example, you can trigger the DAG from the UI. You can do this by going to the `order_analysis_dag` DAG and clicking the "Pause/Unpause" toggle to unpause it. This should trigger the DAG, and you can also trigger new executions by clicking the "Trigger DAG" button.

You can see the logs and monitor the runs in the airflow UI.

You can check the generated CSV data in the [`./data/order_analysis`](./data/order_analysis) folder.

## 7. Accessing the database
You can access the database with the following command (you might need to install `sqlite3`):

```bash
sqlite3 data/api_database.db
```

And once you're in the sqlite shell, you can run queries like:

```sql
SELECT count(*) FROM final_data;
```

## 8. Backfill

To backfill the DAG, you can use the CLI, specifying the start and end dates (change these appropriately):

```bash
docker-compose run --rm webserver airflow \
    dags backfill order_analysis_dag \
    -s 2024-05-30 \
    -e 2024-06-03
```

## 9. Tear down
All the commands in this section can be executed by running an init script:
```bash
./4-teardown.sh
```
But if you prefer to run each command manually, keep reading this section.

We first need to stop the stack and remove associated volumes:

```bash
docker-compose down --volumes
```

If you want to remove the data and logs folders:
```bash
rm -rf ./data ./logs
```

You can also remove the virtual environment:

```bash
deactivate
rm -rf env
```

And all associated docker images and containers (I recommend to use the docker desktop UI for this, as the command line will remove all images and containers, not just the ones related to this project).
