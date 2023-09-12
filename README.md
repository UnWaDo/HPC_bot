# Bot for organization of HPC calculations

## Installation

```bash
pip install virtualenv
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

For Windows change `. venv/bin/activate` to `.\venv\Scripts\Activate.ps1`

If you want to use MySQL as your database, you should also install corresponding driver with `pip install pymysql` or `pip install mysqlclient`

## Configuration

Very simple (and not complete) example of config file is given as `conig_example.json`

- download_path: path to stored files on local computer
- storage: remote cloud storage. Currently only Nextcloud is supported
- log_level: logging level used by `logging` to control output level
- log_file: *(optional)* path to log file. If not given, logs will be printed to console
- bot
  - token: Telegram API token
  - admin_name: username of an administrator
  - log_chat_id: *(optional)* id of a chat to send logging messages
- db: PostgreSQL is expected
  - name: database name
  - connection: configuration of database connection
  - db_type: sqlite, mysql or postgresql. The default is PostgreSQL, so you should install drivers if you intend to use mysql (see Installation section)
- clusters: list of clusters, properties of which are given below
  - label: name of cluster. Must be consistent with database
  - upload_path: where to store files on a cluster
  - runners: list of runners
    - program: name of a program to be launched
    - allowed_args: *(optional)* list of arguments allowed for a program. {} stands for filename
    - default_args: *(optional)* list of standard arguments to be used when no arguments are given
    - associations: *(optional)* list of extensions, associated with the runner
    - description: *(optional)* message to display in /help
  - connection: ssh parameters of the server

## Run

Migrate database (never do this if you are restarting production application). It requires adding `organization.csv` table with columns `label`, `name`, `alias` and `parent` to the root folder, containing required organizations.

```bash
python migrate.py
```

Launch executable

```bash
python run.py
```

## Testing

Testing can be started with `pytest`. Code style may be checked by `pycodestyle HPC_bot` and corrected with `autopep8 -i filename.py`. Note that `-i` flag will modify the file inplace, if you want just to check what will be changed, omit it

## Adding users

Bot can be added to any group by its administrator. Any person in these groups may write to bot in order to get access to calculations. By default, newly registered users are given 5 calculations per month

User can specify its name, surname and organization using `/upd` command. When data is correct, administrator can approve it by sending `/approve` command. After this, user recieve 25 calculations per month