# Postman Collection Exporter

Export your Postman collections via a simple CLI.

---

# 📑 Table of Content

  - [✨ Features](#-features)
  - [🚀 Usage](#-usage)
    - [Export Collections](#-export-collections)
    - [Archive collections](#-archive-collections)
    - [Scheduling CLI actions](#-scheduling-cli-actions)
  - [⚙️ Requirements](#-requirements)
  - [📑 Environment Variables](#-environment-variables)
  - [🛠️ Project Structure](#-project-structure)
  - [🧹 TODO](#-todo)
  - [📜 License](#-license)
  - [👤 Authors](#-authors)


## ✨ Features

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

## 🚀 Usage

### Export Collections
```bash
# Using Python module
python -m postman_collection_exporter.cli export --path /home/user/exports -n Collection1 -n Collection2 --api-key postman-api-key

# Using directly (--api-key is optional if POSTMAN_API_KEY is set)
export-collections --path /home/user/exports -n Collection1 -n Collection2 --api-key postman-api-key
```
- `-p, --path-to-collections`: Directory, where exported collections will be located.
- `-n, --collection-names`: Names of the Postman collections to be export.
- `-k, --api-key`: Optional Postman API key for authentication.  Overrides environment variable.
- `-l, --log-path`: Path to the log file for the command output. [default: /home/username/crontab/cron.log]

### Archive collections
```bash
# Using Python module
python -m postman_collection_exporter.cli archive --path-to-collections /home/user/exports --path-to-archive /home/user/archives -n My_Collections --archive-type tar

# Using directly (--api-key is optional if POSTMAN_API_KEY is set)
archive-collections --path-to-collections /home/user/exports --path-to-archive /home/user/archives -n My_Collections --archive-type tar
```
- `-c, --path-to-collections`: Path to directory with collections being archived.
- `-a, --path-to-archive`: Path to directory with an archive being created.
- `-n, --name`: Name of the archive being created.
- `--archive-type`: Type of an archive being created. [default:zip]
- `-l, --log-path`: Path to the log file for the command output. [default: /home/username/crontab/cron.log]

### Scheduling CLI actions
In order to use scheduling functionality **it's necessary to install** the package with an extra dependency:
```bash
pip install postman_collection_exporter"[schedule]"

# or install needed package later via
pip install python-crontab
```
```bash
# Using Python module
python -m postman_collection_exporter.cli set-schedule --action export --pattern "1 * * * *" --comment "Export Postman collections every hour."

# Using directly
set-schedule --action export --pattern "1 * * * *" --comment "Export Postman collections every hour."
```
- `-a, --action`: Choose the Postman action to schedule. (export or archive at this time) [required]
- `-p, --pattern`: Crontab pattern (e.g., "0 0 * * *" for daily at midnight). Must be written within quotes! [required]
- `-c, --comment`: Comment added to the crontab entry (displayed next to the pattern) [required]
- `-u, --user`: Username for the target crontab (default: current user). Assigning dynamically.
- `--dry-run`: Show the crontab entry that would be created, without applying it.
---

## ⚙️ Requirements

- Python 3.11+

## 📑 Environment Variables

Set the Postman API key as an environment variable (optional):

```bash
export POSTMAN_API_KEY=<actual_api_key>
```

The script will fail gracefully if no API key is found.

---

## 🛠️ Project Structure

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

## 🧹 TODO

- [x] Add unit tests for archiving
- [x] Add unit tests for exporting
- [x] Add logging to CLI command
- [ ] Add logging to helpers functions
- [x] Add unit tests for scheduling
- [ ] Add GitHub Actions CI
- [ ] Add logging

---

## 📜 License
This project is licensed under the MIT License. See the LICENSE file for details.

## 👤 Authors
Sergey Vernigora volt.awp.dev@gmail.com