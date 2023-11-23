# Server 
APIs for interacting with the alert. Pause button, live feed, recording.

## Setup
* Fill out the required variables in `server/.env`

| Variable      | Description | Example | Required |
| ----------- | ----------- | ----------- | ----------- |
| ENCRYPTION_PASSWORD | Random string used to encrypt passwords. Needs to be the same on the client and server. | "abc123efg456" | Required |
| SLACK_API_TOKEN | Slack App Bot User OAuth Token | "xoxb-456789..." | Required |
| BLUEIRIS_API_USER | Blue Iris User | "blueiris_alerts" | Required |
| BLUEIRIS_API_PASSWORD | Blue Iris User Password | "somesecretpassword" | Required |
| BLUEIRIS_WEB_URL | Public URL of Blue Iris Web Server | "https://blueirisdomain.com" | Required |
| LOG_LEVEL | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL, DEBUG | DEBUG | Optional (Default: INFO) |

## WSL Setup
Install Ubuntu From the Microsoft Store
Start Ubuntu Shell:

```bash
## Install Updates and Python 3.11
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.11
sudo echo export PYTHONPATH="/path/to/blueiris_alerts/dir:$PYTHONPATH" >> /etc/bash.bashrc

## Install Poetry
curl -sSL https://install.python-poetry.org | python3.11 -
Add `export PATH="/home/<user>/.local/bin:$PATH"` to your shell configuration file
poetry env use /usr/bin/python3.11

## Install Environment
## Clone repo and run from the root of the blueiris_alerts directory
poetry install

## Activate Environment
poetry shell

## Run Server
poe run_server
```

### Forwarding Port Through WSL
Ubuntu WSL: `ifconfig` (copy IP)
```bash
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8560 connectaddress=<WSL_IP> connectport=8560
netsh advfirewall firewall add rule name="WSL" dir=in action=allow protocol=TCP localport=8560
```

## Docker Setup
* Clone or Download repo
* Run via docker-compose from root of blueiris_alerts directory:
```bash
docker-compose up -d
```

### Updating Docker
* Pull down latest changes
* Build new image and restart:
```bash
docker-compose build
docker-compose up -d
```
