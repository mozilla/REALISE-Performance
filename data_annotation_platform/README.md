# Perf Annotation Changer

This application was originally created to collect annotations of time series data in order to 
construct the [Turing Change Point 
Dataset](https://github.com/alan-turing-institute/TCPD) (TCPD) and we extended it in order to utilize it in the annotation data collection process of our study. [This](https://github.com/alan-turing-institute/annotatechange) is the repository having the code of the original project. Make sure to cite their work in case you will use it.

Here's a screenshot of what the application looks like during the annotation 
process:

![screenshot of Perf Annotation Changer](app/static/img/annotation_ui_example.png)

Some of the features of Perf Annotation Changer include:

* Admin panel to add/remove datasets, add/remove annotation tasks, add/remove 
  users, and inspect incoming annotations.

* Basic user management: authentication, email confirmation, forgotten 
  password, automatic log out after inactivity, etc. Users are only allowed to 
  register using an email address from an approved domain.

* Task assignment of time series to user is done on the fly, ensuring no user 
  ever annotates the same dataset twice, and prioritising datasets that are 
  close to a desired number of annotations.

* Interactive graph of a time series that supports pan and zoom on x and y axis, support for 
  multidimensional time series.

* Mandatory "demo" to onboard the user to change point annotation.

* Backup of annotations to the admin via email.

* Time series datasets are verified upon upload acccording to a strict schema.

* The charcteristics of the timeseries under annotation.



## Getting Started

Below are instructions for setting up the application for local development 
and for running the application with Docker.

### Basic

Perf Annotation Changer can be launched quickly for local development as follows:

1. Clone the repo
   ```
   git clone https://github.com/mozilla/REALISE-Performance.git
   cd REALISE-Performance/data_annotation_platform
   ```

2. Set up a virtual environment and install dependencies (requires Python 
   3.7+)
   ```
   sudo apt-get install -y python3-venv # assuming Ubuntu
   pip install wheel
   python3 -m venv ./venv
   source ./venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create local development environment file
   ```
   cp .env.example .env.development
   sed -i 's/DB_TYPE=mysql/DB_TYPE=sqlite3/g' .env.development
   ```
   With ``DB_TYPE=sqlite3``, we don't have to deal with MySQL locally.

4. Initialize the database (this will be a local ``app.db`` file).
   ```
   ./flask.sh db upgrade
   ```

5. Create the admin user account
   ```
   ./flask.sh admin add --auto-confirm-email
   ```
   The ``--auto-confirm-email`` flag automatically marks the email address of 
   the admin user as confirmed. This is mostly useful in development 
   environments when you don't have a mail address set up yet.

6. Run the application
   ```
   ./flask.sh run
   ```
   This should tell you where its running, probably ``localhost``. You 
   should be able to log in with the admin account you've just created.

7. As admin, upload **ALL** demo datasets (included in [demo_data](./demo_data)) 
   through: Admin Panel -> Add dataset. You should then be able to follow the 
   introduction to the app (available from the landing page).

8. After completing the instruction, you then will be able to access the user 
   interface ("Home") to annotate your own time series.

### Docker

To use Perf Annotation Changer locally using Docker, follow the steps below. For a 
full-fledged installation on a server, see the [deployment 
instructions](./docs/DEPLOYMENT.md).

0. Install [docker](https://docs.docker.com/get-docker/) and 
   [docker-compose](https://docs.docker.com/compose/install/).

1. Clone this repository and switch to it:
   ```
   git clone https://github.com/mozilla/REALISE-Performance.git
   cd REALISE-Performance/data_annotation_platform
   ```

2. Build the docker image:
   ```
   docker build -t datannotationplatform .
   ```

3. Create the directory for persistent MySQL database storage:
   ```
   mkdir -p persist/{instance,mysql}
   sudo chown :1024 persist/instance
   chmod 775 persist/instance
   chmod g+s persist/instance
   ```

4. Copy the environment variables file:
   ```
   cp .env.example .env
   ```
   Some environment variables can be adjusted if needed. For example, 
   when moving to production, you'll need to change the `FLASK_ENV` variable 
   accordingly. Please also make sure to set a proper `SECRET_KEY` and 
   `AC_MYSQL_PASSWORD` (`= MYSQL_PASSWORD`). You'll also need to configure a 
   mail account so the application can send out emails for registration etc. 
   This is what the variables prefixed with ``MAIL_`` are for. The 
   ``ADMIN_EMAIL`` is likely your own email, it is used when the app 
   encounters an error and to send backups of the annotation records. You can 
   limit the email domains users can use with the ``USER_EMAIL_DOMAINS`` 
   variable. See the [config.py](config.py) file for more info on the 
   configuration options.

5. Create a local docker network for communiation between the Perf Annotation Changer 
   app and the MySQL server:
   ```
   docker network create web
   ```

6. Launch the services with docker-compose
   ```
   docker-compose up
   ```
   You may need to wait 2 minutes here before the database is initialized.
   If all goes well, you should be able to point your browser to 
   ``localhost:7831`` and see the landing page of the application. Stop the 
   service before continuing to the next step (by pressing `Ctrl+C`).

7. Once you have the app running, you'll want to create an admin account so 
   you can upload datasets, manage tasks and users, and download annotation 
   results. This can be done using the following command:
   ```
   docker-compose run --entrypoint 'flask admin add --auto-confirm-email' annotatechange
   ```
   Also, you need to load the JSON file cotaining the characteristics of the timeseries.

   ```
   cp ../data/data_timeseries_attributes.json persist/instance/tmp/data_timeseries_attributes.json
   ```

8. As admin, upload **ALL** demo datasets (included in [demo_data](./demo_data)) 
   through: Admin Panel -> Add dataset. You should then be able to follow the 
   introduction to the app (available from the landing page).

9. After completing the instruction, you then will be able to access the user 
   interface ("Home") to annotate your own time series.

## Some implementation details

Below are some thoughts that may help make sense of the codebase.

* Perf Annotation Changer is a web application build on the Flask framework. See [this 
  excellent 
  tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) 
  for an introduction to Flask. The [flask.sh](./flask.sh) shell script loads 
  the appropriate environment variables and runs the application.

* The application handles user management and is centered around the idea of a 
  "task" which links a particular user to a particular time series to 
  annotate.

* An admin role is available, and the admin user can manually assign and 
  delete tasks as well as add/delete users, datasets, etc. The admin user is 
  created using the [cli](./app/cli.py) (see the Getting Started documentation 
  above).

* All datasets must adhere to a specific dataset schema (see 
  [utils/dataset_schema.json](app/utils/dataset_schema.json)). See the files 
  in [demo_data] for examples.

* Annotations are stored in the database using 0-based indexing. Tasks are 
  assigned on the fly when a user requests a time series to annotate (see 
  [utils/tasks.py](app/utils/tasks.py)).

* Users can only begin annotating when they have successfully passed the 
  introduction.

* Configuration of the app is done through environment variables, see the 
  [.env.example](.env.example) file for an example.

* Docker is used for deployment (see the deployment documentation in 
  [docs](docs)), and [Traefik](https://containo.us/traefik/) is used for SSL, 
  etc.

* The time series graph is plotted using [d3.js](https://d3js.org/).
