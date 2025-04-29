# Postman Collection Exporter

Export your Postman collections via a simple CLI.

---

## ✨ Features

- **Export Multiple Collections**: Export several Postman collections simultaneously with just a few commands.
- **Archive Collections in Known Formats**: Archive exported Postman collections to formats like `tar`, `zip`, `gztar`, `bztar`, and `xztar`.
- **Asynchronous API Interaction**: Leverages `asyncio`, `httpx`, and `aiofiles` for efficient, non-blocking communication with the Postman API.
- **Save Collections in JSON Format**: Save Postman collections locally in a clean, standardized JSON format.
- **CLI Built with asyncclick Library**: A powerful and user-friendly command-line interface, built with `asyncclick` to handle async operations gracefully.
- **Error Handling**: Gracefully handles errors from the Postman API, ensuring that authentication issues or rate limits are reported clearly.
- **Modular and Extendable**: The app's modular structure makes it easy to add new features or adjust behavior as needed.

---

## 🚀 Usage

### Export Collections
```bash
# Using directly (--api-key is optional if POSTMAN_API_KEY is set)
python -m postman_collection_exporter.cli export --path /home/user/exports -n Collection1 -n Collection2 --api-key postman-api-key

# Using CLI command (--api-key is optional if POSTMAN_API_KEY is set)
export-collections --path /home/user/exports -n Collection1 -n Collection2 --api-key postman-api-key
```
- `-p, --path-to-collections`: Directory, where exported collections will be located.
- `-n, --collection-names`: Names of the Postman collections to be export.
- `-k, --api-key`: Optional Postman API key for authentication.  Overrides environment variable.

### For archive collections
```bash
# Using directly (--api-key is optional if POSTMAN_API_KEY is set)
python -m postman_collection_exporter.cli archive --path-to-collections /home/user/exports --path-to-archive /home/user/archives -n My_Collections --archive-type tar

# Using CLI command
archive-collections --path-to-collections /home/user/exports --path-to-archive /home/user/archives -n My_Collections --archive-type tar
```
- `-c, --path-to-collections`: Path to directory with collections being archived.
- `-a, --path-to-archive`: Path to directory with an archive being created.
- `-n, --name`: Name of the archive being created.
- `--archive-type`: Type of an archive being created.[default:zip]
---

## ⚙️ Requirements

- Python 3.11+
- Install dependencies:

```bash
pip install -r requirements.txt
```

Or if you're using Poetry:

```bash
poetry install
```

---

## 📑 Environment Variables

Export API key into terminal via command (optional):

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
└── src
    └── postman_collection_exporter
        ├── cli.py
        ├── enums.py
        ├── exceptions.py
        ├── exporters.py
        ├── helpers.py
        └── __init__.py
```
---

## 🧹 TODO

- [ ] Add unit tests
- [ ] Add GitHub Actions CI
- [ ] Improve logging

---

## 📜 License
This project is licensed under the MIT License. See the LICENSE file for details.

## 👤 Authors
Sergey Vernigora volt.awp.dev@gmail.com