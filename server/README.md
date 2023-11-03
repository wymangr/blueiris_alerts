# Server 

### WSL Setup
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
poetry install

## Activate Environment
poetry shell
```

### todo:
- Add More Server Documentation