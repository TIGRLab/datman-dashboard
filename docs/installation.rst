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
If you're considering this you should be prepared for a long installation
process. Note that all the example paths and installation commands provided
below are for Ubuntu 20.04 and may differ if you're using another operating
system.

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
     described below. For more information and a list of all settings see
     `here `_
     
     
     
     ^^^^^^^^^^
     
     
     
     
     
   * Install uwsgi (on ubuntu this is just ``apt install uwsgi``). On some
   operating systems you may also need to install the uwsgi python3 plugin.
   For Ubuntu 20.04 this can be done with `apt install uwsgi-plugin-python3`.
   Note that you may have to reboot your computer after installing the python3
   plugin to get uwsgi to correctly use it.

   Then create your configuration file for uwsgi to use. On Ubuntu 20.04, for
   example, you would make a file at `/etc/uwsgi/apps-enabled/dashboard.ini`.

   In the 'dashboard.ini' file you should add at least the following
   configuration.

   .. code-block:: ini

      [uwsgi]

      module = wsgi:app
      chown-socket = www-data
      lazy-apps = True     # Needed to prevent the scheduler from locking up
      # Need the python3 plugin to run python3 apps
      plugins = python3,logfile

      # This should be the path to your copy of the dashboard
      chdir = PATH_TO_YOUR_DASHBOARD_HERE
      # This is the virtualenv uwsgi will use when running the dashboard
      virtualenv = PATH_TO_YOUR_VIRTUALENV_HERE

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

#. Install nginx. On Ubuntu 20.04 you can do this with `sudo apt install nginx`.
   Then in the 'sites-enabled' folder add a file named 'dashboard.conf' with
   your site configuration. On Ubuntu 20.04 you can add the file at
   `/etc/nginx/sites-enabled/dashboard.conf`. At a minimum, you should
   add a server entry with your site name and at least the below configuration.
   Note that this configuration is for HTTP only, and shouldn't be used outside
   of a private network.

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
