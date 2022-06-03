-------
Plugins
-------

Installing Plugins
------------------
The dashboard's functionality can easily be extended with blueprints. Copy
the blueprint you want to add into ```datman-dashboard/dashboard/blueprints`` 
and restart uwsgi to complete installation. The blueprint itself should document 
any new environment variables to set, python packages to install, or databases 
to create.


Creating a Plugin
-----------------
To create your own blueprint you should do the following:

#. Define a `flask blueprint <https://flask.palletsprojects.com/en/2.1.x/blueprints/>`_
#. Define a ``register_bp`` function that accepts an app object and, at a
   minimum, calls ``app.register_blueprint(your_bp_here)``. This function 
   is an ideal place to add any configuration your plugin needs to 
   the ``app.config`` dictionary. It's also where you'd want to add any 
   alternate databases to the ``app.config['SQLALCHEMY_BINDS']`` dictionary
