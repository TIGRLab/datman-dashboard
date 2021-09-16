------------
Installation
------------

You have several options for how to run the QC dashboard and these are
listed below.

#. `Run a development instance`_
#. `Run with Docker Compose`_
#. `Do a Full install`_


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



Do a Full install
-----------------
A full install gives you the most control over your configuration. If you're
considering this you should be prepared for a long installation process. Note
that all the example paths and installation commands provided below are for
Ubuntu 20.04 and may differ if you're using another operating system.

#. `Install Datman <http://imaging-genetics.camh.ca/datman/installation.html>`_
   and set up its configuration files.
#. Clone the `QC dashboard. <https://github.com/TIGRLab/dashboard.git>`_

   .. code-block:: bash

      git clone https://github.com/TIGRLab/dashboard.git
#. Install the dashboard's python dependencies. Note that the dashboard is
   meant to run on python 3.5 or higher.

   .. code-block:: bash

      # Make a virtual environment
      python3 -m venv $YOUR_ENV_PATH/venv

      # Activate your environment
      source $YOUR_ENV_PATH/venv/bin/activate

      # Install required packages
      pip install -r $DASHBOARD_PATH/requirements.txt
#. Set up `PostgreSQL. <https://www.postgresql.org/download/>`_ The
   dashboard was tested against PostgreSQL 12 and all examples below assume
   this is the version in use. Newer versions should work as well, however.

   * Install PostgreSQL.

     .. code-block:: bash

        sudo apt install postgresql-12

   * Make postgres use a more secure password storage method.

     * Open the ``postgresql.conf`` file. e.g. ``nano /etc/postgresql/12/main/postgresql.conf``
     * Uncomment the line for the ``password_encryption`` setting
     * Change it to ``password_encryption = scram-sha-256``

   * Allow the dashboard user to connect to the dashboard database with a password.

     * Open the ``pg_hba.conf`` file. e.g. ``nano /etc/postgresql/12/main/pg_hba.conf``
     * Beneath the comment that says "Put your actual configuration here", add
       an entry like this::

        #     database name  database user     connection method
        local dashboard      dashboard         scram-sha-256
     * Reload the configuration files to make the changes take effect.

       .. code-block:: bash

          sudo systemctl reload postgresql

     * Add the dashboard user to the database.

       .. code-block:: bash

          # Save the password you use. You'll use it every
          # time you connect to the database.
          sudo -u postgres createuser -P dashboard
   * Initialize the database.

     * Create an empty database that's owned by the dashboard user.

       .. code-block:: bash

          sudo -u postgres createdb -O dashboard dashboard

     * Activate your virtual environment, if you havent yet.

       .. code-block:: bash

          source $YOUR_ENV_PATH/venv/bin/activate

     * Set the environment variables needed for flask migrate to run.

       .. code-block:: bash

          # Replace "/full/path/to/datman" with the full
          # path to your datman folder.
          export PATH=/full/path/to/datman:${PATH}
          export PYTHONPATH=/full/path/to/datman:${PYTHONPATH}

          # This secret key is needed but is temporary
          # so can be anything for now
          export FLASK_SECRET_KEY=mytemporarysecretkey

          export POSTGRES_USER=dashboard
          export POSTGRES_PASS=YOUR_DATABASE_PASSWORD_HERE

     * Switch to your dashboard directory and run the command below to create
       the database tables.

       .. code-block:: bash

          flask db upgrade

#. Get an OAuth client ID and client secret `from GitHub. <https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app>`_
   In the 'Authorization callback URL' field be sure to add ``/callback/github``
   to the end of your homepage URL.

   You'll need to provide the Client ID and Client Secret to the dashboard
   later so be sure to record them.

#. Configure the uWSGI server.

   * Install uWSGI.

     .. code-block:: bash

        sudo apt install uwsgi

        # On some platforms (such as Ubuntu 20.04) you also
        # need the python3 plugin. After installation you
        # may need to restart your computer
        sudo apt install uwsgi-plugin-python3
   * Create a ``dashboard.ini`` config file in uWSGI's apps-enabled folder.
     (e.g. ``/etc/uwsgi/apps-enabled/dashboard.ini``)

   * Add your configuration. At a minimum you should add the settings
     described below. For more information and a list of all dashboard settings
     see :ref:`here. <glossary>` Any Datman settings you need should also be
     added here. For a list of uWSGI options see their documentation
     `here <https://uwsgi-docs.readthedocs.io/en/latest/Options.html>`_

     .. code-block:: ini

        [uwsgi]

        module = wsgi:app
        chown-socket = www-data
        plugins = python3,logfile

        # Needed to prevent the scheduler from locking up
        lazy-apps = True

        # This should be the path to your dashboard folder
        chdir = PATH_TO_YOUR_DASHBOARD_HERE
        # This is the virtualenv uwsgi will use when
        # running the dashboard
        virtualenv = PATH_TO_YOUR_VIRTUALENV_HERE

        # This controls the user and group the app will run under.
        # Replace it with a real username/group.
        uid = YOURUSER
        gid = YOURGROUP

        # Dashboard + Datman env variables can be set here
        # Below shows only the minimum required variables that
        # must be set to run the app.

        # Set this to something unguessable and keep it private
        # or user sessions will be compromised
        env = FLASK_SECRET_KEY=YOUR_VERY_SECURE_KEY_HERE

        env = POSTGRES_USER=dashboard
        env = POSTGRES_PASS=YOUR_DATABASE_PASSWORD

        env = OAUTH_CLIENT_GITHUB=YOUR_GITHUB_CLIENT_ID
        env = OAUTH_SECRET_GITHUB=YOUR_GITHUB_SECRET

        # Configure datman here too
        env = PYTHONPATH=PATH_TO_YOUR_DATMAN_FOLDER_HERE
        env = DM_SYSTEM=YOUR_SYSTEM_NAME
        env = DM_CONFIG=PATH_TO_YOUR_MAIN_CONFIG_HERE

   * Restart uWSGI to force it to re-read the configuration.

     .. code-block:: bash

        sudo systemctl restart uwsgi

#. Configure nginx to serve the uWSGI dashboard app.

   * Install nginx

     .. code-block:: bash

        sudo apt install nginx

   * Add a ``dashboard.conf`` file to nginx's sites-enabled folder.
     (e.g. ``/etc/nginx/sites-enabled/dashboard.conf``)

     At a minimum you should add a server entry, like the one shown below,
     with your server's name filled in. Note that this example configuration
     is for HTTP only and should not be used outside of a private network.

     .. code-block:: bash

        server {
          listen 80;
          server_name localhost YOURSERVERNAMEHERE;

          location / {
            include uwsgi_params;
            uwsgi_pass unix://var/run/uwsgi/app/dashboard/socket;
          }
        }



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
