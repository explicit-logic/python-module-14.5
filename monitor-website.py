import os
import requests
import smtplib
import paramiko
import pydo
import schedule
import time
from dotenv import load_dotenv

load_dotenv()

DO_API_TOKEN = os.getenv('DO_API_TOKEN')
DROPLET_ID = os.getenv('DROPLET_ID')
DROPLET_IP = os.getenv('DROPLET_IP')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_FROM = 'onboarding@resend.dev'
EMAIL_TO = EMAIL_FROM
IMAGE_NAME='nginx'

SSH_PRIVATE_KEY_PATH=os.getenv('SSH_PRIVATE_KEY_PATH')

def send_notification(email_msg):
  print('Sending an email...')
  with smtplib.SMTP('smtp.resend.com', 587) as smtp:
      smtp.starttls()
      smtp.ehlo()
      smtp.login(SMTP_USER, SMTP_PASSWORD)
      message = f"From: {EMAIL_FROM}\nTo: {EMAIL_TO}\nSubject: SITE DOWN\n\n {email_msg}"
      smtp.sendmail(EMAIL_FROM, EMAIL_TO, message)

def restart_container():
  print('Restarting the application...')
  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  ssh.connect(hostname=DROPLET_IP, username='root', key_filename=SSH_PRIVATE_KEY_PATH)
  stdin, stdout, stderr = ssh.exec_command(f'docker ps -aq --filter "ancestor={IMAGE_NAME}"')
  container_ids = stdout.read().decode().splitlines()
  container_id = container_ids[0]
  stdin, stdout, stderr = ssh.exec_command(f'docker start {container_id}')
  print(stdout.readlines())
  ssh.close()

def restart_server_and_container():
  print('Rebooting the server...')
  client = pydo.Client(token=DO_API_TOKEN)
  action = client.droplet_actions.post(DROPLET_ID, body={'type': 'reboot'})['action']
  action_id = action['id']
  while True:
    status = client.actions.get(action_id=action_id)['action']['status']
    print(f'action status: {status}')
    if status == 'in-progress':
      time.sleep(3)
    else:
      break

  while True:
    droplet = client.droplets.get(droplet_id=DROPLET_ID)["droplet"]
    status = droplet['status']
    print(f"droplet status: {droplet['status']}")

    if status == 'active':
      time.sleep(15)
      restart_container()
      break

    time.sleep(5)

def monitor_application():
  try:
    response = requests.get(f"http://{DROPLET_IP}:8080")

    if response.status_code == 200:
      print('Application is running successfully!')
    else:
      print('Application Down. Fix it!')
      msg = f"Application returned {response.status_code}."
      send_notification(msg)
      restart_container()
  except Exception as ex:
    print(f"Connection error happened: {ex}")
    msg = f"Application not accessible at all."
    send_notification(msg)
    restart_server_and_container()

schedule.every(5).minutes.do(monitor_application)

while True:
  schedule.run_pending()
  time.sleep(1)
