# Alyx-local

Experimental Neuroscience Laboratories metadata and data manager - **Made easy for local installation**

**Disclaimer :**  
Alyx-local is a fork from the original codebase, available here : [https://github.com/cortex-lab/alyx](https://github.com/cortex-lab/alyx), that is still and currentely developped by the [International Brain Laboratory](https://www.internationalbrainlab.com/) and the [Cortical Processing Lab](https://www.ucl.ac.uk/cortexlab) (Matteo Carandini and Kenneth Harris) at UCL.
The original paper mentionning the use of this data architecture for uniformisation in neursciences laboratories is [published here](https://www.nature.com/articles/s41592-022-01742-6).

Alyx was developped for their own purpose - facilitating data management and facilitating collaboration in an institute spatially distributed over the world - as well as for benefitting the scientific community. 
Before you decide to install and use ours or teir version of Alyx, i advise giving a look at their work wich is updated more regularly and with more humanpower, rather than using this local-specific version. Our version is very focues on single lab and simple local installations, as explained in the rationale below.


## Rationale

This version of Alyx is walinkg in the steps of the original Alyx experimental data manager, but is focused solely on unning inside a set of docker containers (a docker composition) to make it easy to maintain and run anywhere. It doesn't rely on a specific worldwide infrastructure involving service providers, as the original alyx database did. Hence, this version is trying to mostly **simplify** the maintenance and initial deployment of Alyx, for labs with a local data infrastructure.

This version is originally developped to have the simple ability to run this great database to manage a single lab's data, using the local Information Systems architecture, local file servers (using smb) and local network. (no certificates needed)

## Installation

To install it localy, you first need to clone this repository to your local machine, or the machine that you want the Alyx server to run on.

It is ideal that you use [git](https://git-scm.com/downloads) for the cloning / updating of your database.

### **Clone** this repository into your computer : 

- by using your command line interface, navigate to the folder where you want your installation files to sit (anywhere in your Documents folder is a location that would make sense). Usually using the `cd Myfolder/mysubfolder` command.

- do `git clone https://github.com/JostTim/haiss-alyx.git`

- swtich to the docker branch by doing `git fetch --all` (to fetch all changes to the docker branch and all the others branches) then `git checkout docker` (to sitch to the docker branch that you now have the info about)

### **Configure** your installation :

- by using [`pdm`](https://pdm-project.org/en/latest/), a package manager that will make things much easier. Please see [how to install pdm](https://pdm-project.org/en/latest/#recommended-installation-method) if you don't have it already.
- Ensure your terminal's current directory is again in the folder where you cloned the repository, previously (by using  `cd`)
- Ensure you have python 3.12 installed. If you are onwindows, and easy way is to go on the Windows Store and just type python 3.10, then install it.
- do ``pdm install``. Pdm should start installing the necessary packages locally, and should select the python version that is appropriate for this install. If not, please manually select the proper one using ``pdm use``.
- Now, you should have the utility scripts designed to ease Alyx configuration, de ployment and maintenance available. You can check them by doing `pdm run --list`
- Start the ``configure`` script by running ``pdm run configure``
- This script shall walk you through the configuration process, and generate the necessary config files in the config folder of the repository you cloned from github. You can edit those as will afterwards, if you require additionnal changes. This repository is not managed via git, so you can add / remove / change things in this repository without worrying about pulling changes from the source github repository to get updates, at a later time, and your files are not stored online (as they may contain sensitive passwords, etc.)

### **Deploy** locally on Docker

- You will need [Docker Desktop](https://www.docker.com/products/docker-desktop/) for this part, please ensure you downloaded it and that the virtualization engine works for your machine (disable/install/troubleshoot WSL2 if it does not work, for some users on windows 10). Please also note that installing docker desktop might require you to have the latest updates on your operating system, so please ensure you did these updates.
- Again, ensure your terminal's current directory is again in the folder where you cloned the repository, previously (by using  `cd`)
- using previously installed ``pdm`` you will be able tu run the utility scripts that wrap around docker commands, to install and orchestration of containers decribed througout the docker's ``compose.yml`` file, and the `docker` folder. See in the section containers below for explanation of the roles of each containter service used here.
- Start by doing `pdm run fresh-build`.
- This will start by pulling the linux images necessary for the containers to run, and then instanciate them correctly as decribed in the docker compose and docker files.
- If everything runs correctly, you should end up with a message similar to : 

    ```log
    django_server  | Starting Gunicorn to serve django alyx...
    django_server  | [2024-12-09 13:13:38 +0000] [309] [INFO] Starting gunicorn 23.0.0
    django_server  | [2024-12-09 13:13:38 +0000] [309] [INFO] Listening at: http://0.0.0.0:8000 (309)
    django_server  | [2024-12-09 13:13:38 +0000] [309] [INFO] Using worker: sync
    django_server  | [2024-12-09 13:13:38 +0000] [310] [INFO] Booting worker with pid: 310 (the number here is not important and may be different when you run this)
    ```

Possible errors :
- If you get an error similar to : 
    ```log
    error during connect : Get ....
    open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
    ```
    It means that the docker desktop service is not launched. Please make sure the docker desktop application you installed previously is running.

### Turn **off**, **restart** and **maintain**
    
- To turn off the containers, you can run anytime from a terminal the command `pdm run stop`, wile the current working directory of your terminal is at the root of the repository you cloned from github.
- To start it again, you can run `pdm run start`. Please note that this will not work if you didn't had a successfull build previously of if you deleted previously built-containers or volumes. (see online for info about what is a docker volume)
- To re-build it after changes, but not deleting current data saved through volumes, you can run `pdm run build`. This can cause unpredictible results as you need to know what you do, so this command is particulary usefull for developement, but for a simple useage, working with `backup` files and using the `pdm run fresh-build` command is advised instead.

- Mainteance can be performed using the commands ``pdm run interact`` and ``pdm run manage``. Again these are most usefull for developement and should not be necessary for simple use.


## Backups

This section will be detailed soon. Basically the backup/restore process will be done unsing [Django Db-Backup](https://django-dbbackup.readthedocs.io/en/stable/) plugin, wich makes this very easy and parametrable.

## Containers 

The containers are lightweight linux virtualized instances that run separately, can share ressources (mounted folders, local network, etc) and execute a service. Each container has the role to execute a given service, and Alyx require several services to be up simultaneously and work in concert, to work correctly.

1. The first container, `django_server` one is the one that does most of the work, and runs our **web application**, in python, using the Django package. The source code of the package running there is located is the ``/src/alyx`` folder in the folder you cloned from the github repository.

2. Because Django is a dynamic servig application, it is not meant to serve static files (like images, javascript source code files, css styling files etc..) that don't change whatever the moment and context you access them. For this purpose, we need a static-serving container, `nginx_server`. This is the actual service that we hit when connecting to alyx with http (port 80 is the standard http port). It's configuration is to serve files (without autherntication required, so take care of what you put in these folders) from the folders in ``/static`` and ``/media`` that are located in ``/docker/templates/uploaded``. It also proxies requests to the `django_server` (that is served on port 8000 in the local network betweeen containers), to the port 80, if the url starts with anything else than /static or /media.

3. We next have the burried core of the system, the PostgreSQL database running container, `postgres_db` wich is used by `django_server` internally to access, store, and query subselections of the metadata in a fast way. All the work of creating, deleting, modifying the database tables is handled in python, with django, wich has the role of doing the ORM (for Object Relational Mapping, wich stands for mapping a relational database, like SQL to a set of object oriented data items, like python can be). Such creation and modification of the database through django is called ``migration` and this is a whole topic in itself, wich you can know more about [here](https://docs.djangoproject.com/en/5.1/topics/migrations/).

4. The last service is `rabbitmq` which is a fast [networked message queue broker](https://www.rabbitmq.com/). This one is optional, and can be used if you configure a celery based distributed set of workers that Alyx can use to start computer intensive programs remotely on various machines. This is still in early beta. If it fails to launch and you don't intent to use Alyx for this purpose, you should not pay attention to it.
