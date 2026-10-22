"""
Lanza el job de EMR de forma efímera (R4, R10, R11).

- Termina cualquier clúster activo que haya quedado encendido.
- Sube etl_vuelos.py a S3.
- Crea un clúster de 3 x m4.large (único tipo permitido) con un único step y
  KeepJobFlowAliveWhenNoSteps=False: el clúster se apaga solo al terminar el step,
  tanto si sale bien como si falla.

Uso:  python emr/run_emr.py
"""
import os
import time
from pathlib import Path

import boto3

REGION = "us-east-1"
BUCKET = "s3vuelosparcial"
SCRIPT_KEY = "EMR/etl_vuelos.py"
SUBNET = "subnet-0615d7b82ad53f510"

emr = boto3.client("emr", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

# 1. Apagar clústeres activos (R10)
active = emr.list_clusters(ClusterStates=["STARTING", "BOOTSTRAPPING", "RUNNING", "WAITING"])["Clusters"]
if active:
    ids = [c["Id"] for c in active]
    print("Terminando clústeres activos:", ids)
    emr.terminate_job_flows(JobFlowIds=ids)

# 2. Subir el job
s3.upload_file(str(Path(__file__).with_name("etl_vuelos.py")), BUCKET, SCRIPT_KEY)
print(f"Subido s3://{BUCKET}/{SCRIPT_KEY}")

# 3. Clúster efímero con un step
resp = emr.run_job_flow(
    Name="vuelos-etl",
    # Misma versión que ya se usó en esta cuenta; se puede cambiar con EMR_RELEASE.
    ReleaseLabel=os.environ.get("EMR_RELEASE", "emr-spark-8.0.0"),
    Applications=[{"Name": "Spark"}],
    LogUri="s3://aws-logs-627221105870-us-east-1/elasticmapreduce/",
    Instances={
        "InstanceGroups": [
            {"Name": "Master", "InstanceRole": "MASTER", "InstanceType": "m4.large", "InstanceCount": 1},
            {"Name": "Core", "InstanceRole": "CORE", "InstanceType": "m4.large", "InstanceCount": 2},
        ],
        "Ec2SubnetId": SUBNET,
        "Ec2KeyName": "vockey",
        "KeepJobFlowAliveWhenNoSteps": False,
        "TerminationProtected": False,
    },
    Steps=[{
        "Name": "etl_vuelos",
        "ActionOnFailure": "TERMINATE_CLUSTER",
        "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": ["spark-submit", "--deploy-mode", "cluster",
                     f"s3://{BUCKET}/{SCRIPT_KEY}", "--bucket", BUCKET],
        },
    }],
    ServiceRole="EMR_DefaultRole",
    JobFlowRole="EMR_EC2_DefaultRole",
    VisibleToAllUsers=True,
)
cluster_id = resp["JobFlowId"]
print("Clúster creado:", cluster_id)

# 4. Esperar a que termine
while True:
    c = emr.describe_cluster(ClusterId=cluster_id)["Cluster"]
    state = c["Status"]["State"]
    steps = emr.list_steps(ClusterId=cluster_id)["Steps"]
    step_state = steps[0]["Status"]["State"] if steps else "-"
    print(time.strftime("%H:%M:%S"), "cluster:", state, "| step:", step_state)
    if state.startswith("TERMINATED"):
        break
    time.sleep(30)

print("Motivo:", c["Status"]["StateChangeReason"])
print("Horas normalizadas:", c.get("NormalizedInstanceHours"))
if step_state != "COMPLETED":
    print("El step NO terminó bien; revisar logs en", c.get("LogUri"))
