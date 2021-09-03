------------
Installation
------------

You have several options for how to install and use the QC dashboard. These are
listed below from easiest to hardest. If you want to setup a development
environment you should instead see this section:  `Run for development`_

#. `Run with Docker Compose`_. This is the fastest and simplest method
   (but offers the least customization).
#. `Run with Docker and your own PostgreSQL database`_. This allows you to
   connect the QC dashboard to a pre-existing database server.
#. `Run without containers`_. This will take the most effort but allow you
   to fully customize your build.

Run with Docker compose
---------------------
#. `Install Docker <https://docs.docker.com/get-docker/>`_, if you don't
   already have it.
#. `Install Datman. <http://imaging-genetics.camh.ca/datman/installation.html>`_
#. Clone the `QC dashboard. <https://github.com/TIGRLab/dashboard.git>`_

   .. code-block:: bash

      git clone https://github.com/TIGRLab/dashboard.git
#. Switch to the 'containers' folder inside the dashboard's folder.

   .. code-block:: bash

      cd dashboard/containers
#. Fill in your configuration in the ``dashboard/containers/dashboard.env`` file.
   At a minimum you should set a flask secret key (this should be a very hard
   to guess string), your OAuth secret key and OAuth client key
   `from GitHub, <https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app>`_
   and a database password. For information on configuring the dashboard
   :ref:`see here <glossary>`
#. Fill in your database configuration in the ``dashboard/containers/database.env``
   file. Note that the database name, user, and password should match what you
   provided in dashboard.env
#. Run the app

   .. code-block:: bash

      docker compose up


Run with Docker and your own PostgreSQL database
------------------------------------------------
#. `Install Docker <https://docs.docker.com/get-docker/>`_, if you don't
already have it.

Run without containers
----------------------
If you're considering this you should be familiar with configuring postgres
and uwsgi.

#. `Install Datman. <http://imaging-genetics.camh.ca/datman/installation.html>`_
#. Clone the `QC dashboard. <https://github.com/TIGRLab/dashboard.git>`_

   .. code-block:: bash

      git clone https://github.com/TIGRLab/dashboard.git
#. Install the dashboard's python dependencies. Note that the dashboard is
   meant to run on python 3.5 or higher.

   .. code-block:: bash

      # Make a virtual environment
      python -m venv $YOURPATH/venv

      # Activate your environment
      source $YOURPATH/venv/bin/activate

      # Install required packages
      pip install -r $DASHBOARDPATH/requirements.txt
#. `Install PostgreSQL <https://www.postgresql.org/download/>`_ and add a
    database user for the dashboard. The dashboard was tested against PostgreSQL
    12 but more recent versions should work as well. On Ubuntu 20.04 you can
    install postgres with the following:

    .. code-block:: bash

       sudo apt install postgresql-12

    First, you should update `postgresql.conf` to use a more secure method
    for user passwords. On Ubuntu 20.04, for version 12, this file is stored at
    `/etc/postgresql/12/main/postgresql.conf`.

    In this file, change `password_encryption = md5` to
    `password_encryption = scram-sha-256` and ensure the line is not commented
    out.

    Next, you'll want to update the `pg_hba.conf` file to allow password
    protected connections to the dashboard. On Ubuntu 20.04 this file is
    at `/etc/postgresql/12/main/pg_hba.conf`. Adding the line below to this
    file (beneath the comment section that says "Put your actual configuration
    here") will let you securely login to the dashboard user from your local
    machine with the password you set. If you plan to use a different name
    for your dashboard user you should modify the third column to match this
    username.

    .. code-block:: bash

       #     database name  database user     connection method
       local dashboard      dashboard         scram-sha-256

    After you've made these changes you must reload the configuration files.
    On Ubuntu you can do this with `sudo systemctl reload postgresql`

    Next you should add a dashboard user to postgres. You should set
    a password for this user. This password and user is what the dashboard
    will use to connect to the database, so keep track of them.

    .. code-block:: bash

       sudo -u postgres createuser -P dashboard

    Once your database is ready you can initialize an empty database with the
    correct schema with the following:

    .. code-block:: bash

       sudo -u postgres createdb -O dashboard dashboard


    ***** Is this actually needed on prod / devel? *************************
    ***** Likely not needed (and on prod it uses * but probably only because of
    ***** datman/psql )

    You'll need to update `postgresql.conf`, which is stored at
    `/etc/postgresql/12/main/postgresql.conf` for version 12 on Ubuntu 20.04,
    to make postgres listen for your machine's IP in addition to localhost.

    .. code-block:: bash

       listen_addresses = 'YOUR IP HERE', localhost
    ********************************************************

    ***** Are pg_hba.conf records needed? ******************
    ***** Only if dashboard will be using non-local connections also
    ***** (e.g. datman/psql)

    ***** Are pg_ident.conf records needed? ****************
    *****


    ***** These steps should come after the env vars are set (otherwise
          flask migrate fails)



    The first time you set up postgres for the dashboard you also need to
    initialize its database tables. You can do this by:
      1. changing to the directory where you cloned the dashboard
      2. Making sure your python virtual env is active
      3.
       # You must be in the dashboard folder when you run this
       export PATH=<datmanpath>:${PATH}
       export PYTHONPATH=<datmanpath>:${PYTHONPATH}
       export FLASK_SECRET_KEY=something
       export POSTGRES_USER=
       export POSTGRES_PASS=
       flask db upgrade

#. Get an OAuth client key and OAuth secret key `from GitHub. <https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app>`_
   You'll need to provide these to the dashboard later.
#. Install uwsgi (on ubuntu this is just ``apt install uwsgi``). On some
   operating systems you may also need to install the uwsgi python3 plugin.
   For Ubuntu 20.04 this can be done with `apt install uwsgi-plugin-python3`.
   Then create your configuration file for uwsgi to use. On Ubuntu 20.04, for
   example, you would make a file at `/etc/uwsgi/apps-enabled/dashboard.ini`.

   In the 'dashboard.ini' file you should add at least the following
   configuration.

   .. code-block::ini

      [uwsgi]

      module = wsgi:app
      chown-socket = www-data
      lazy-apps = True     # Needed to prevent the scheduler from locking up

      # This should be the path to your copy of the dashboard
      chdir = PATH_TO_YOUR_DASHBOARD_HERE
      # This is the virtualenv uwsgi will use when running the dashboard
      virtualenv = PATH_TO_YOUR_VIRTUALENV_HERE
      # Need the python3 plugin to run python3 apps
      plugins = python3,logfile

      # Fill in the path where you want log files to go. The default
      # below is for Ubuntu 20.04. Note that this log will hold messages from
      # the dashboard app only and using it will turn off log messages from
      # uWSGI itself. So if you're having issues starting the app you should
      # comment out this line to regain those messages.
      logger = file:/var/log/uwsgi/app/dashboard.log

      # This controls the user and group the app will run as. Replace it with
      # a real user.
      uid = YOURUSER
      gid = YOURGROUP

    Below this you should add all the environment variables that the dashboard
    needs to run. At a minimum you'll need to set the variables from the
    config glossary

    *********INSERT REFERENCE TO GLOSSARY*******

    that have been identified as required, though you may wish to enable
    other dashboard features as well. Below is an example of what the
    bare minimum environment configuration in your 'dashboard.ini' may need
    to contain, but you should consult the configuration glossary for more
    information.

    .. code-block::ini

       env = FLASK_SECRET_KEY=YOUR_VERY_SECURE_KEY_HERE

       env = POSTGRES_USER=YOUR_DATABASE_USER
       env = POSTGRES_PASS=YOUR_DATABASE_PASSWORD

       env = OAUTH_CLIENT_GITHUB=YOUR_GITHUB_CLIENT_ID
       env = OAUTH_SECRET_GITHUB=YOUR_GITHUB_SECRET

    You will also need to provide the required datman configuration in this
    file. Consult

    ******** INSERT LINK TO DATMAN CONFIG DOCS HERE *******

    datman's config docs for more info. The below should be sufficient for
    the dashboard's purposes though.

    .. code-block::ini

       env = PYTHONPATH=PATH_TO_YOUR_DATMAN_COPY_HERE
       env = DM_SYSTEM=YOUR_SYSTEM_NAME
       env = DM_CONFIG=PATH_TO_YOUR_MAIN_CONFIG_HERE

    Then, restart uwsgi to force it to read the configuration. On Ubuntu
    you can do this with `sudo systemctl restart uwsgi`.





#. Install nginx

Run for development
-------------------








-v ${base}/datman-config:/config
-v ${base}/temp_workdir:/archive
-v ${base}/dashboard/logs:/logs


docker run -it -p 5000:5000 -e FLASK_SECR_KEY=testingkey dashboard:0.1 uwsgi --socket 0.0.0.0:5000 --protocol http --wsgi-file /dashboard/wsgi.py --callable app --enable-threads


Should use the setuser option like with datman to ensure
changes to archive dont change owner to root:root

Should maybe see if you can run it better than with wsgi.py... lots of
settings will differ from ours

Need to document all from the ini_template / config folder
  - Ensure reasonable defaults


Have a 'debug' tag that disables oauth login and mounts in a local
copy of the dashboard so it can be changed on the fly ...?

Need way to initialize the postgresql database (once app running it might
  not be possible...)

Need to document how to backup the volume of postgres data

Need to document how to run nginx in front of it

Need to make sure the way app is running is production not flask builtin server


Installation cases:
  1. Docker compose
  2. Dashboard container with fully external/user set-up postgres
  3. Fully manual install
  4. debug / dev install

2.
  To access host based services (postgres installed on host):
      Set POSTGRES_SRVR = host.docker.internal
  Ensure a user exists in your database with a username matching POSTGRES_USER
  and password matching POSTGRES_PASS
