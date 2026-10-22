"""
Despliega backend + frontend en UN solo EC2 t3.small (R1, R2, R8, R9, R11).

  - Sistema operativo: Ubuntu 24.04 (usuario de SSH: "ubuntu").
  - FastAPI sirve la API, "/" (cliente) y "/manager" (panel gerencial) en el puerto 8000.
  - RDS, S3, EMR y Athena siguen donde estan; el EC2 llama a Athena con LabInstanceProfile
    (sin claves guardadas en el servidor).

Uso (desde la raiz del repo):
  python deploy/deploy_ec2.py              # crea el EC2 (o muestra el que ya existe)
  python deploy/deploy_ec2.py --recreate   # termina el actual y crea uno nuevo con el codigo actualizado
  python deploy/deploy_ec2.py --terminate  # lo termina (para no gastar presupuesto)

Nota: el zip que se sube a S3 incluye backend/.env (credenciales de RDS). El bucket es privado.
"""
import argparse
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import boto3

REGION = "us-east-1"
BUCKET = "s3vuelosparcial"
ZIP_KEY = "deploy/app.zip"
NAME = "vuelos-backend"
SG_NAME = "vuelos-backend-sg"
PORT = 8000
INSTANCE_TYPE = "t3.small"   # R11: t3 micro/small/medium permitidos
PROFILE = "LabInstanceProfile"
KEY_NAME = "vockey"

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"__pycache__", ".venv", "venv", ".git"}

ec2 = boto3.client("ec2", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
ssm = boto3.client("ssm", region_name=REGION)

# Script que Ubuntu ejecuta UNA vez, como root, la primera vez que arranca la maquina ("user data").
# Su salida queda en /var/log/user-data.log dentro del servidor.
USER_DATA = r"""#!/bin/bash
exec > /var/log/user-data.log 2>&1
set -ex
export DEBIAN_FRONTEND=noninteractive

# 1. Paquetes del sistema: python3-venv (entornos virtuales) y unzip
apt-get update
apt-get install -y python3-venv unzip

# 2. Carpeta de la app y entorno virtual (las librerias quedan aisladas del sistema)
mkdir -p /opt/app && cd /opt/app
python3 -m venv venv
./venv/bin/pip install boto3

# 3. Bajar el codigo desde S3. El EC2 usa el rol LabInstanceProfile, por eso no hacen falta claves.
./venv/bin/python -c "import boto3; boto3.client('s3', region_name='__REGION__').download_file('__BUCKET__', '__ZIP_KEY__', 'app.zip')"
unzip -o app.zip
./venv/bin/pip install -r backend/requirements.txt

# 4. Registrar la API como servicio de systemd: arranca sola con la maquina y se reinicia si falla
cat > /etc/systemd/system/vuelos.service <<'EOF'
[Unit]
Description=Vuelos API
After=network.target

[Service]
WorkingDirectory=/opt/app/backend
ExecStart=/opt/app/venv/bin/uvicorn main:app --host 0.0.0.0 --port __PORT__ --workers 1
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now vuelos
echo "USER-DATA-DONE"
"""


def find_instances(states=("pending", "running", "stopping", "stopped")):
    r = ec2.describe_instances(Filters=[
        {"Name": "tag:Name", "Values": [NAME]},
        {"Name": "instance-state-name", "Values": list(states)},
    ])
    return [i for res in r["Reservations"] for i in res["Instances"]]


def build_and_upload_zip():
    tmp = Path(__file__).with_name("app.zip")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for folder in ("backend", "frontend"):
            for p in (ROOT / folder).rglob("*"):
                rel = p.relative_to(ROOT)
                if p.is_dir() or SKIP_DIRS & set(rel.parts) or p.suffix == ".pyc":
                    continue
                z.write(p, rel.as_posix())
    s3.upload_file(str(tmp), BUCKET, ZIP_KEY)
    print(f"zip subido a s3://{BUCKET}/{ZIP_KEY} ({tmp.stat().st_size / 1024:.0f} KB)")
    tmp.unlink()


def ensure_security_group():
    vpc = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"][0]["VpcId"]
    found = ec2.describe_security_groups(Filters=[
        {"Name": "group-name", "Values": [SG_NAME]}, {"Name": "vpc-id", "Values": [vpc]}])["SecurityGroups"]
    if found:
        return found[0]["GroupId"]
    sg = ec2.create_security_group(GroupName=SG_NAME, Description="Vuelos API (puerto 8000)", VpcId=vpc)["GroupId"]
    ec2.authorize_security_group_ingress(GroupId=sg, IpPermissions=[{
        "IpProtocol": "tcp", "FromPort": PORT, "ToPort": PORT,
        "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "API y frontend"}]}])
    print("security group creado:", sg)
    return sg


def pick_subnet():
    subs = ec2.describe_subnets(Filters=[{"Name": "default-for-az", "Values": ["true"]}])["Subnets"]
    return sorted(subs, key=lambda s: s["AvailabilityZone"])[0]["SubnetId"]


def terminate():
    ids = [i["InstanceId"] for i in find_instances()]
    if ids:
        ec2.terminate_instances(InstanceIds=ids)
        ec2.get_waiter("instance_terminated").wait(InstanceIds=ids)
        print("terminado:", ids)
    else:
        print("no hay instancia", NAME)


def wait_health(ip, timeout=420):
    url = f"http://{ip}:{PORT}/health"
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(10)
    return False


def report(ip):
    print(f"\nListo: http://{ip}:{PORT}/        (cliente)")
    print(f"       http://{ip}:{PORT}/manager (panel)")
    print(f"       http://{ip}:{PORT}/docs")
    print("\nEn parcial2-harness/config.yaml:")
    print(f'  backend:  base_url: "http://{ip}:{PORT}"')
    print(f'  frontend: base_url: "http://{ip}:{PORT}"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recreate", action="store_true")
    ap.add_argument("--terminate", action="store_true")
    args = ap.parse_args()

    if args.terminate:
        return terminate()

    existing = find_instances()
    if existing and not args.recreate:
        i = existing[0]
        print("ya existe", i["InstanceId"], i["State"]["Name"], i.get("PublicIpAddress"))
        if i["State"]["Name"] == "running":
            report(i["PublicIpAddress"])
        return
    if existing:
        terminate()

    build_and_upload_zip()
    sg = ensure_security_group()
    # AMI = la "imagen" del sistema operativo. Canonical publica el id de la ultima Ubuntu 24.04 en SSM.
    ami = ssm.get_parameter(Name="/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id")["Parameter"]["Value"]
    user_data = (USER_DATA.replace("__BUCKET__", BUCKET).replace("__ZIP_KEY__", ZIP_KEY)
                 .replace("__REGION__", REGION).replace("__PORT__", str(PORT)))

    inst = ec2.run_instances(
        ImageId=ami, InstanceType=INSTANCE_TYPE, MinCount=1, MaxCount=1,
        KeyName=KEY_NAME, IamInstanceProfile={"Name": PROFILE}, UserData=user_data,
        NetworkInterfaces=[{"DeviceIndex": 0, "SubnetId": pick_subnet(), "Groups": [sg],
                            "AssociatePublicIpAddress": True}],
        TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": NAME}]}],
    )["Instances"][0]
    iid = inst["InstanceId"]
    print("creando", iid, INSTANCE_TYPE, "...")
    ec2.get_waiter("instance_running").wait(InstanceIds=[iid])
    ip = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]["PublicIpAddress"]
    print("IP publica:", ip, "- esperando que la API responda (instala dependencias, ~3-5 min)...")

    if wait_health(ip):
        report(ip)
    else:
        print("La API no respondio a tiempo. Log de arranque:")
        out = ec2.get_console_output(InstanceId=iid, Latest=True).get("Output", "")
        print(out[-3000:] or "(consola aun sin salida; reintenta en un minuto)")
        sys.exit(1)


if __name__ == "__main__":
    main()
