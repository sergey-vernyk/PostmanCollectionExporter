# Postman Collection Exporter

Export your Postman collections into local JSON files via a simple CLI.

---

## 🚀 Usage

```bash
python src/export.py --path exported_collections -n Collection1 -n Collection2
```

- `--path` / `-p`: Path to the directory where collections will be saved.
- `--collection-names` / `-n`: Names of the collections to export (you can pass multiple).

Example:
```bash
python src/json_exporter.py -p exported_collections -n Collection1 -n Collection2
```
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

Create a `.env` file and provide your Postman API key:

```env
POSTMAN_API_KEY=your-postman-api-key-here
```

The script will fail gracefully if no API key is found.

---

## 🛠️ Project Structure

```
.
├── exported_collections
├── pyproject.toml
├── README.md
├── requirements.txt
└── src
    ├── exceptions.py
    ├── __init__.py
    └── json_exporter.py
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


