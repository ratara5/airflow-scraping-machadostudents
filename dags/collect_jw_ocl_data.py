from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.models import Variable

from datetime import datetime, date
import docker

def check_if_container_exists(container_name):
    client = docker.from_env()
    # container_name = "scraping_postgres_test_v2"
    try:
        container = client.containers.get(container_name)
        if container.status == 'exited':
            return True  # The container exists and is stopped
        else:
            return False  # The container exists, but is not stopped
    except docker.errors.NotFound:
        return False  # The container doesn't exist

def decide_container_action(**kwargs):
    ti = kwargs['ti']
    container_exists = ti.xcom_pull(task_ids='check_container_exists')
    
    if container_exists:
        return 'restart_postgres'  # Restart container
    else:
        return 'run_scraping_postgres'  # Run container



default_args={
    "start_date": datetime(2024, 1, 1),
    "depends_on_past": False
}

dag_config = Variable.get("collect_jw_ocl_data_config", deserialize_json=True)
postgres_host = dag_config["postgres_host"]
postgres_db = dag_config["postgres_db"]
postgres_user = dag_config["postgres_user"]
postgres_password = dag_config["postgres_password"]




with DAG(dag_id="jw_ocl_guide",
         description="Collect Data Program OCL",
         schedule_interval="0 10 10 2,4,6,8,10,12 *", # -> At 10 am of day 10th february, april, june, august, october, december
         catchup=False, # If False -> past instances will be not executed
         default_args=default_args,
         max_active_runs=1) as dag:
    
    
    
    # List all tasks except clear_logs
    tasks_to_clean = [task.task_id for task in dag.tasks if task.task_id != 'clear_logs']

    # Clear logs command
    clean_command = ' && '.join([f'rm -rf /opt/airflow/logs/{{{{ dag.dag_id }}}}/{{{{ task_id }}}}/*' for task_id in tasks_to_clean])

    t1 = BashOperator(
        task_id = 'show_vars',
        bash_command=f'echo "{dag_config}"'
    )
    
    clear_logs = BashOperator(
        task_id='clear_logs',
        bash_command=clean_command,
    )

    check_container_task = PythonOperator(
        task_id="check_container_exists",
        python_callable=check_if_container_exists,
        op_kwargs={'container_name':f'{postgres_host}'},
        dag=dag
    )

    branch_task = BranchPythonOperator(
        task_id='decide_container_action',
        provide_context=True,
        python_callable=decide_container_action,
        dag=dag
    )

    restart_postgres = BashOperator(
        task_id='restart_postgres',
        bash_command=f'docker restart {postgres_host}', #scraping_postgres_v2
        dag=dag
    )

    run_scraping_postgres = DockerOperator(
        task_id='run_scraping_postgres',
        image='my_postgres_image_v2:latest',  # The image of your postgres service
        container_name=postgres_host, #'scraping_postgres_v2',
        #api_version='auto',
        auto_remove=False,
        command="postgres",  # Command to execute in container
        docker_url="unix://var/run/docker.sock",  # Connection to docker in host machine
        network_mode="scraping_airflow_network",  # Shared network between containers
        mount_tmp_dir=False,
        environment={
            'POSTGRES_USER': postgres_user,# os.getenv('AIRFLOW_VAR_POSTGRES_USER'),
            'POSTGRES_PASSWORD': postgres_password, # os.getenv('AIRFLOW_VAR_POSTGRES_PASSWORD'),
            'POSTGRES_DB': postgres_db # os.getenv('AIRFLOW_VAR_POSTGRES_DB')
        }
    )

    check_postgres_ready = BashOperator(
        task_id='check_postgres_ready',
        bash_command=f'until nc -z -v -w30 {postgres_host} 5432; do echo "Waiting for PostgreSQL..."; sleep 5; done', #scraping_postgres_v2
        trigger_rule=TriggerRule.ALWAYS
        #dag=dag,
    )

    """
    wait_for_data = PostgresSensor(
        task_id='wait_for_data',
        postgres_conn_id='postgres_scraping_conn',  # El ID de la conexión a PostgreSQL configurado en Airflow
        sql="SELECT COUNT(1) FROM my_table WHERE condition_column = 'value';",
        mode='poke',  # También puedes usar 'reschedule' para mayor eficiencia
        timeout=60,  # Tiempo máximo de espera en segundos
        poke_interval=20,  # Intervalo entre chequeos
    )
    """

    """
    continue_task = BashOperator(
        task_id='continue_task',
        bash_command='true',
        
    )
    """

    """
    stop_scraping_postgres = BashOperator(
    task_id='stop_scraping_postgres',
    bash_command="docker stop scraping_postgres_test_v2", # scraping_postgres_test_v2
    """

    run_scraping_script = DockerOperator(
        task_id='run_scraping_script',
        image='my_scraping_image_v2:latest',  # The image of your scraping service
        #container_name='my_new_scraping_container_v2',
        #api_version='auto',
        auto_remove=True,
        command="python /app/main.py", # Command to execute in container
        docker_url="unix://var/run/docker.sock",  # Connection to docker in host machine
        network_mode="scraping_airflow_network",  # Shared network between containers
        mount_tmp_dir=False,
        environment={
            'POSTGRES_USER': postgres_user, #os.getenv('AIRFLOW_VAR_POSTGRES_USER'),
            'POSTGRES_PASSWORD': postgres_password, #os.getenv('AIRFLOW_VAR_POSTGRES_PASSWORD'),
            'POSTGRES_DB': postgres_db #os.getenv('AIRFLOW_VAR_POSTGRES_DB')
        }
    )

    stop_postgres = BashOperator(
        task_id='stop_postgres',
        #bash_command="docker exec scraping_postgres_v2 pg_ctl stop", #-D /var/lib/postgresql/data
        #bash_command="docker exec scraping_postgres_v2 bash -c \"su postgres -c 'pg_ctl stop -D /var/lib/postgresql/data -m fast'\""
        #bash_command="docker exec scraping_postgres_v2 bash -c \"su postgres -c 'pg_ctl stop -D /var/lib/postgresql/data -m fast && while pg_isready -q; do sleep 1; done'\""
        
        #bash_command="docker exec scraping_postgres_v2 bash -c \"su postgres -c 'pg_ctl stop -D /var/lib/postgresql/data -m fast && until [ \$(docker inspect -f '{{ '{{' }}.State.Status{{ '}}' }}' scraping_postgres_v2) == 'exited' ]; do sleep 1; done'\""

        bash_command=f'docker stop {postgres_host}' # scraping_postgres_v2

    )

    t1 >> clear_logs >> check_container_task >> branch_task
    branch_task >> [run_scraping_postgres, restart_postgres] >> check_postgres_ready >> run_scraping_script >> stop_postgres