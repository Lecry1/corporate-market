# corporate-market
Летняя практика в ivi

# Настройка окружения разработчика
## Создание виртуального окружения

```bash
python -m venv .venv
````

### Linux/macOS

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

## Установка зависимостей

```bash
pip install -r requirements-dev.txt
```

## Установка Git hooks

```bash
pre-commit install
```
