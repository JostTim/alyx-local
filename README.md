# alyx

[![Github Actions](https://github.com/cortex-lab/alyx/actions/workflows/main.yml/badge.svg)](https://github.com/cortex-lab/alyx/actions/)
[![Coverage Status](https://coveralls.io/repos/github/cortex-lab/alyx/badge.svg?branch=github_action)](https://coveralls.io/github/cortex-lab/alyx?branch=master)


Database for experimental neuroscience laboratories

## Installation

This version of Alyx is meant to run on docker, and on docker alone. (for better maintainability and developement cycle) 
It has not been tested for a raw run on linux.

- Install docker desktop
- Install pdm
- Clone this repository
- Change directory to inside the directory you just cloned
- run `pdm install`
    - You will have a virtual environment created under the .venv folder, in your cloned folder.
- Now that the venv and dependancies are installed on your machine, create the final config files necessary four your alyx installation on docker, with the command : `pdm run install_docker_alyx`
- Follow the instructions, and enter a password for the database (press enter if the randomly generated one is okay) It will be saved in a file as advertized so don't worry to copy it elsewhere.
- now that everything should be ready, run : `docker compose up --build`
- If the creating of the container(s) worked fine, you should see : `Starting Gunicorn to serve django alyx...` `Starting gunicorn 23.0.0` `Listening at: http://0.0.0.0:8000 (111)` `Using worker: sync` `Booting worker with pid: 112`
- Open a browser tab at `http://localhost/admin` to see alyx's graphical interface.
- If this is your first connection and you didn't had a backup restored upon build, you can first conenct with user : admin , passowrd : admin. Otherwise, use your regular credential from the backup image.
- Done, you may now proceed to more adwanced steps (such as interfacing your alyx docker setver with python) following other links.


## Contribution

* Development happens on the **dev** branch
* alyx is sync with the **master** branch
* alyx-dev is sync with the **dev** branch
* Migrations files are provided by the repository
* Continuous integration is setup, to run tests locally:
    -   `./manage.py test -n` test without migrations (faster)
    -   `./manage.py test` test with migrations (recommended if model changes)

```
$ /manage.py test -n
```
