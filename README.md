Tracking model changes across M2M relationships
===============================================

    $ virtualenv --no-site-packages ve
    $ source ve/bin/activate
    (ve)$ pip install -r requirements.pip
    (ve)$ cd example_project
    (ve)$ ./manage.py test app

Guiding principles
==================

1. Master doesn't need to know what slaves are replicating data.
2. Master always keeps a grand master copy of all data.
3. Slaves maintain duplicated, perhaps expanded, data set.