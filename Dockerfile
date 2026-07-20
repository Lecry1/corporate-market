# Используем легковесный образ Python 3.12 
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь оставшийся код проекта
COPY . .

# Команда, которая будет выполняться при старте контейнера
CMD ["python", "CorpMarket/manage.py", "runserver", "0.0.0.0:8000"]