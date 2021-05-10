----------------------
Configuration Glossary
----------------------

Listed below are all configuration values that may be set for the QC dashboard.
They're organized into sections based on the feature that they configure.
These values should be set in your shell (or your uWSGI configuration file).

Cluster
*******
Allow the dashboard to make use of a computing cluster (e.g. 
`Slurm <https://slurm.schedmd.com/documentation.html>`_). These can be left
unset if a queue is unavailable.
