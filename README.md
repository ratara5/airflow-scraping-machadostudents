# AIRFLOW FOR SCRAPING

Contains dockerized airflow in order to execute scraping by using DockerOperator with two images:
scraping service and postgres service

## Table of contents

- [Installation](#installation)
- [Usage](#usage)
- [Contribution](#contribution)
- [License](#license)

## Installation
Official documentation in:<br>
https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html

### each time
bash <br>
```docker compose up```

### airflow in virtual environment
bash<br>
```python3 -m venv airflow-env```<br>
```source airflow-env/bin/activate```<br>
```pip install --upgrade pip setuptools wheel```<br>
```pip install apache-airflow```


### is pip being executed in virtual enviroment?
bash<br>
```which pip```

### if you experiment issues with virtual environment
bash<br>
```deactivate # Exit from current environment, if it's active```<br>
```rm -rf airflow-env  # Delete problematic virtual environment ```<br>
```python3 -m venv airflow-env```<br> 
```source airflow-env/bin/activate```

### Install Airflow
bash<br>
```pip install --upgrade pip setuptools wheel```<br>
```pip install apache-airflow```

### Enable DockerOperator class
bash<br>
```pip install apache-airflow-providers-docker```

### Add more directories in .env (optional)
.env<br>
```AIRFLOW__CORE__DAGS_FOLDER=```

### Add more directories in docker-compose.yaml (optional)
docker-compose
```
x-airflow-common:
 volumes:
    - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags

    - ${AIRFLOW_PROJ_DIR:-.}/dags/other1:/opt/airflow/dags/other1
    - ${AIRFLOW_PROJ_DIR:-.}/dags/other2:/opt/airflow/dags/other2
    - ${AIRFLOW_PROJ_DIR:-.}/dags/other3:/opt/airflow/dags/other3
```

## Usage
Previously, you must had built the images for scraping service and for postgres service.<br>
Warning!: There must not be containers based on these images running.

## Contribution

## License