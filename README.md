# Postman Collection Exporter

Export your Postman collections via a simple CLI

---

# Table of Content

  - [Features](#features)
  - [Usage](#usage)
    - [Installation](#installation)
    - [Export Collections](#export-collections)
    - [Archive collections](#archive-collections)
    - [Scheduling CLI actions](#scheduling-cli-actions)
  - [Requirements](#requirements)
  - [Environment Variables](#environment-variables)
  - [Project Structure](#project-structure)
  - [Contributing](#contributing)
  - [TODO](#todo)
  - [License](#license)


## Features

- **Export Multiple Collections**: Export several Postman collections simultaneously with just a few commands.
- **Archive Collections in Known Formats**: Archive exported Postman collections to formats like `tar`, `zip`, `gztar`, `bztar`, and `xztar`.
- **Asynchronous API Interaction**: Leverages `asyncio`, `httpx`, and `aiofiles` for efficient, non-blocking communication with the Postman API.
- **Save Collections in JSON Format**: Save Postman collections locally in a clean, standardized JSON format.
- **CLI Built with asyncclick Library**: A powerful and user-friendly command-line interface, built with `asyncclick` to handle async operations gracefully.
- **Error Handling**: Gracefully handles errors from the Postman API, ensuring that authentication issues or rate limits are reported clearly.
- **Modular and Extendable**: The app's modular structure makes it easy to add new features or adjust behavior as needed.
- **Crontab Scheduling (Unix-based Systems)**: Automate exporting or archiving actions using crontab. This feature is only available on Unix-based systems and requires an additional dependency.
- **Logging**: Logs CLI command results and errors to a user-specified log file (via the `--log-path` option).  
---

## Usage


### Installation
```bash
$ pip install postman_collection_exporter

# or if you intended to use scheduling 
$ pip install "postman_collection_exporter[schedule]"

# or install needed package later via
$ pip install python-crontab
```

### Export Collections
```bash
# Using Python module
$ python -m postman_collection_exporter.cli export --path /home/user/exports -n Collection1 -n Collection2 --api-key postman-api-key

# Using directly (--api-key is optional if POSTMAN_API_KEY is set)
$ export-collections --path /home/user/exports -n Collection1 -n Collection2 --api-key postman-api-key
```
- `-p, --path-to-collections`: Directory, where exported collections will be located.
- `-n, --collection-names`: Names of the Postman collections to be export.
- `-k, --api-key`: Optional Postman API key for authentication.  Overrides environment variable.
- `-l, --log-path`: Path to the log file for the command output. [default: /home/username/crontab/cron.log]

### Archive collections
```bash
# Using Python module
$ python -m postman_collection_exporter.cli archive --path-to-collections /home/user/exports --path-to-archive /home/user/archives -n My_Collections --archive-type tar

# Using directly (--api-key is optional if POSTMAN_API_KEY is set)
$ archive-collections --path-to-collections /home/user/exports --path-to-archive /home/user/archives -n My_Collections --archive-type tar
```
- `-c, --path-to-collections`: Path to directory with collections being archived.
- `-a, --path-to-archive`: Path to directory with an archive being created.
- `-n, --name`: Name of the archive being created.
- `--archive-type`: Type of an archive being created. [default:zip]
- `-l, --log-path`: Path to the log file for the command output. [default: /home/username/crontab/cron.log]

```bash
# Using Python module
$ python -m postman_collection_exporter.cli set-schedule --action export --pattern "1 * * * *" --comment "Export Postman collections every hour."

# Using directly
$ set-schedule --action export --pattern "1 * * * *" --comment "Export Postman collections every hour."
```
- `-a, --action`: Choose the Postman action to schedule. (export or archive at this time) [required]
- `-p, --pattern`: Crontab pattern (e.g., "0 0 * * *" for daily at midnight). Must be written within quotes! [required]
- `-c, --comment`: Comment added to the crontab entry (displayed next to the pattern) [required]
- `-u, --user`: Username for the target crontab (default: current user). Assigning dynamically.
- `--dry-run`: Show the crontab entry that would be created, without applying it.
---

### Scheduling CLI actions

```bash
# Using Python module
$ python -m postman_collection_exporter.cli set-schedule --action export --pattern "1 * * * *" --comment "Export Postman collections every hour."

# Using directly
$ set-schedule --action export --pattern "1 * * * *" --comment "Export Postman collections every hour."
```
- `-a, --action`: Choose the Postman action to schedule. (export or archive at this time) [required]
- `-p, --pattern`: Crontab pattern (e.g., "0 0 * * *" for daily at midnight). Must be written within quotes! [required]
- `-c, --comment`: Comment added to the crontab entry (displayed next to the pattern) [required]
- `-u, --user`: Username for the target crontab (default: current user). Assigning dynamically.
- `--dry-run`: Show the crontab entry that would be created, without applying it.

```bash
# Using Python module
$ python -m postman_collection_exporter.cli get-schedules --all

# Using directly
$ get-schedules --all
```
- `-a, --all`: Show all available crontab schedules, ignoring pattern and user filters.
- `-p, --pattern`: Filter schedules by crontab pattern (e.g., "0 0 * * *" for daily at midnight). 
- `-u, --user`: Username for the target crontab (default: current user). Assigning dynamically.

## Requirements

- Python 3.11+

## Environment Variables

Set the Postman API key as an environment variable (optional):

```bash
$ export POSTMAN_API_KEY=<actual_api_key>
```

### Note: 
Exporting `POSTMAN_API_KEY` will have an effect only with manual exporting collection(s). In order to schedule exporting collections it's necessary to pass API key via `api-key` option like below:

```bash
$ set-schedule --action export --comment "comment" --pattern "* * * * *"

Please, fill out params to schedule for the <export> command. Continue? [Y/n]: 
==> path (required): path
==> collection-names (required): name
Any other value for 'collection-names'? [y/N]: N
==> api-key []: # pass here your API-key (it will be hidden)
# other prompts
```
---
## Project Structure

```
.
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements.txt
├── src
│   └── postman_collection_exporter
│       ├── cli.py
│       ├── dependencies
│       │   ├── __init__.py
│       │   └── utils.py
│       ├── enums.py
│       ├── exceptions.py
│       ├── exporters.py
│       ├── helpers.py
│       ├── __init__.py
│       ├── logging
│       │   ├── config.py
│       │   └── __init__.py
│       ├── scheduling
│       │   ├── cli.py
│       │   ├── crontab_helpers.py
│       │   ├── __init__.py
│       │   └── utils.py
│       └── structures.py
└── tests
    ├── fixtures
    │   ├── test_data_collection_1.json
    │   └── test_data_collection_2.json
    ├── __init__.py
    ├── mocks.py
    ├── test_crontab_helpers.py
    └── test_helpers.py
```
---

## Contributing
We welcome contributions of all kinds — bug fixes, new features, documentation improvements, or suggestions!

**To contribute:**
- Fork this repository to your own GitHub account.
- Clone your fork locally and create a new branch:

```bash
$ git clone https://github.com/sergey-vernyk/PostmanCollectionExporter.git
$ git checkout -b my-feature-branch
```
- Make your changes and follow the existing coding style.
- Test your changes if applicable.
- Commit your changes with a clear message:

```bash
$ git commit -m "Add brief description of changes"
```
- Push your branch to your fork:

```bash
$ git push origin my-feature-branch
```
- Open a **Pull Request** from your branch to the main repository, explaining what you changed and why.

We appreciate all contributions and will review pull requests as quickly as possible. Be respectful and constructive when interacting with others in this project.

## TODO

- [x] Add unit tests for archiving
- [x] Add unit tests for exporting
- [x] Add logging to CLI command
- [ ] Add logging to helpers functions
- [x] Add unit tests for scheduling
- [x] Add GitHub Actions CI
- [ ] Add logging

## License
This project is licensed under the MIT License. See the LICENSE file for details.