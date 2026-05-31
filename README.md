# Module 14 - Automation with Python

This repository contains a demo project created as part of my **DevOps studies** in the [TechWorld with Nana – DevOps Bootcamp](https://www.techworld-with-nana.com/devops-bootcamp).

**Demo Project:** Website Monitoring and Recovery

**Technologies used:** Python, DigitalOcean, Docker, Linux

**Project Description:**

- Create a server on a cloud platform
- Install Docker and run a Docker container on the remote server
- Write a Python script that monitors the website by accessing it and validating the HTTP response
- Write a Python script that sends an email notification when website is down
- Write a Python script that automatically restarts the application & server when the application is down

---

## Prerequisites

- [Python 3.12+](https://www.python.org/downloads/) and [uv](https://docs.astral.sh/uv/) for dependency management
- An AWS account with permissions to manage EC2 instances, EBS volumes and snapshots
- [Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) — the AWS SDK for Python ([EC2 client reference](https://docs.aws.amazon.com/boto3/latest/reference/services/ec2.html))
- [schedule](https://schedule.readthedocs.io/) — for running the backups on a recurring basis

Install Python dependencies:

```shell
uv sync
```

---

### Overview

![](./images/overview.png)


### Create a droplet on DigitalOcean

RAM: 2GB

Assign created public SSH key from your computer

![](./images/create-droplet.png)


Connect to the droplet
```sh
ssh root@<DROPLET-IP>
```

Check OS:

```sh
cat /etc/os-release 
```

![](./images/os-release.png)

### Install Docker and run a Docker container on the remote server

Install docker

https://docs.docker.com/engine/install/ubuntu


Run `nginx` image
```sh
docker run -d -p 8080:80 nginx
```

Open in your browser: `<DROPLET-IP>:8080`

![](./images/nginx.png)


### Write a Python script that monitors the website by accessing it and validating the HTTP response

```py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

droplet_ip = os.getenv('DROPLET_IP')
response = requests.get(f"http://{droplet_ip}:8080")

if response.status_code == 200:
  print('Application is running successfully!')
else:
  print('Application Down. Fix it!')
```

Set env variables:

```sh
cp .env.example .env
```

Run
```sh
python3 monitor-website.py
```

![](./images/monitor-app.png)

### Write a Python script that sends an email notification when website is down

- Create `resend` account

https://resend.com/settings/smtp
https://resend.com/api-keys

![](./images/resend-api-key.png)


Set:
```conf
SMTP_USER=resend
SMTP_PASSWORD=YOUR_API_KEY
```

```python
import os
import requests
import smtplib
from dotenv import load_dotenv

load_dotenv()

DROPLET_IP = os.getenv('DROPLET_IP')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_FROM = 'onboarding@resend.dev'
EMAIL_TO = EMAIL_FROM
response = requests.get(f"http://{DROPLET_IP}:8080")

with smtplib.SMTP('smtp.resend.com', 587) as smtp:
  smtp.starttls()
  smtp.ehlo()
  smtp.login(SMTP_USER, SMTP_PASSWORD)
  msg = f"From: {EMAIL_FROM}\nTo: {EMAIL_TO}\nSubject: SITE DOWN\n\nFix the issue! Restart the application."
  smtp.sendmail(EMAIL_FROM, EMAIL_TO, msg)
```

- Check email sending is working

Run
```sh
python3 monitor-website.py
```

Check your inbox on resend:

![](./images/email-delivered.png)

Stop the `nginx` container

```sh
docker ps
docker stop <NGINX-CONTAINER-ID>
```

- Add handling of exceptions

```py
import os
import requests
import smtplib
from dotenv import load_dotenv

load_dotenv()

DROPLET_IP = os.getenv('DROPLET_IP')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_FROM = 'onboarding@resend.dev'
EMAIL_TO = EMAIL_FROM

def send_notification(email_msg):
  with smtplib.SMTP('smtp.resend.com', 587) as smtp:
      smtp.starttls()
      smtp.ehlo()
      smtp.login(SMTP_USER, SMTP_PASSWORD)
      message = f"From: {EMAIL_FROM}\nTo: {EMAIL_TO}\nSubject: SITE DOWN\n\n {email_msg}"
      smtp.sendmail(EMAIL_FROM, EMAIL_TO, message)

try:
  response = requests.get(f"http://{DROPLET_IP}:8080")
  if response.status_code == 200:
    print('Application is running successfully!')
  else:
    print('Application Down. Fix it!')
    msg = f"Application returned {response.status_code}."
    send_notification(msg)
except Exception as ex:
  print(f"Connection error happened: {ex}")
  msg = f"Application not accessible at all."
  send_notification(msg)
```

Run
```sh
python3 monitor-website.py
```

![](./images/not-accessible-email.png)

### Write a Python script that automatically restarts the application & server when the application is down


Add a full path of your private ssh key to `SSH_PRIVATE_KEY_PATH` in `.env` file


Check connection

```py
   print('Application Down. Fix it!')
    msg = f"Application returned {response.status_code}."
    send_notification(msg)
    ssh= paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=DROPLET_IP, username='root',key_filename=SSH_PRIVATE_KEY_PATH)
    stdin, stdout, stderr = ssh.exec_command('docker ps')
    print(stdout.readlines())
    ssh.close()
```

![](./images/check-ssh-connect.png)


Create read/write token on DigitalOcean:

https://cloud.digitalocean.com/account/api/tokens/new

![](./images/do-token.png)

Set a newly created token to `DO_API_TOKEN` env var

- Get id of your droplet

Go to `cloud.digitalocean.com` and click on your droplet.
Look at the browser address bar. The URL looks like:
```
https://cloud.digitalocean.com/droplets/123456789
                                          ^^^^^^^^^
```
That number (123456789) is your droplet ID.

Set `DROPLET_ID` env var

Stop the `nginx` container

```sh
docker ps
docker stop <NGINX-CONTAINER-ID>
```

```py
  client = pydo.Client(token=DO_API_TOKEN)
  client.droplet_actions.post(DROPLET_ID, body={'type': 'reboot'})
```


Run
```sh
python3 monitor-website.py
```

Check your droplet dashboard:

![](./images/droplet-reboot.png)

Check the final code: [monitor-website.py](./monitor-website.py)

![](./images/demo.gif)
