# Postman Collection Exporter

Export your Postman collections into local JSON files via a simple CLI.

---

## ✨ Features

- **Export Multiple Collections**: Export several Postman collections simultaneously with just a few commands.
- **Asynchronous API Interaction**: Leverages asyncio, httpx, aiofiles for efficient, non-blocking communication with the Postman API.
- **Save Collections in JSON Format**: Save Postman collections locally in a clean, standardized JSON format.
- **CLI Built with asyncclick library**: A powerful and user-friendly command-line interface, built with asyncclick to handle async operations gracefully.
- **Error Handling**: Gracefully handles errors from the Postman API, ensuring that authentication issues or rate limits are reported clearly.
- **Modular and Extendable**: The app's modular structure makes it easy to add new features or adjust behavior as needed.

## 🚀 Usage

```bash
# using direct main function (--api-key is optional)
python src/cli.py --path /home/user/exports -n Collection1 -n Collection2 --api-key postman-api-key 
# using CLI command (--api-key is optional)
export-postman --path /home/user/exports -n Collection1 -n Collection2 --api-key postman-api-key
```

- `--path` / `-p`: Path to the directory where collections will be saved.
- `--collection-names` / `-n`: Names of the collections to export (you can pass multiple).
- `--api-key` / `-k`: Postman API key for authentication.

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
├── pyproject.toml
├── README.md
├── requirements.txt
└── src
    ├── cli.py
    ├── exceptions.py
    ├── exporters.py
    ├── helpers.py
    └── __init__.py
```

---

## ❗ Error Handling

- If authentication fails (invalid/expired API key), a friendly error will be printed and the program will exit.
- Other common Postman API errors are handled as well.

---

## 🧹 TODO

- [x] Add unit tests
- [x] Add GitHub Actions CI
- [x] Improve logging

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Authors
Sergey Vernigora volt.awp.dev@gmail.com