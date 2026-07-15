# 🛒 КорпМаркет (CorpMarket)

> **Проект разработан в рамках летней практики в компании ivi.**  
> Внутренняя площадка компании для размещения объявлений о продаже товаров, предоставлении услуг и поиске попутчиков между сотрудниками.

---

## 🚀 Quick Start 
1. **Настройка файла окружения**
   
   Создайте файл `.env` в корне проекта на основе `.env.example`:

   ```env
   SECRET_KEY=your_secret_key
   DEBUG=True

   DB_NAME=corporate_market
   DB_USER=corpmarket_user
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

2. **Соберите образ и поднимите контейнеры в фоновом режиме:**
   ```bash
   docker-compose up -d --build
   ```

3. **Выполните миграции внутри контейнера:**

   ```bash
   docker-compose exec web python CorpMarket/manage.py migrate
   ```


3. **Загрузите готовые тестовые данные (фикстуры):**
   ```bash
   ./fixture_restore.sh
   ```
   [См.Подробнее](#тестирование-и-работа-с-бд)


   **Или создайте нового администратора вручную (если не использовали фикстуры):**
   ```bash
   docker-compose exec web python CorpMarket/manage.py createsuperuser
   ```



После запуска приложение будет доступно по адресу: **http://127.0.0.1:8000/**

* Посмотреть общие логи: `docker compose logs -f`
* Логи конкретных контейнеров: `docker compose logs -f web` или `docker compose logs -f db`
* Остановить проект: `docker compose down -v`

---

## 🛠 Стек технологий

* **Backend:** Python 3.12, Django 6
* **Database:** PostgreSQL 16+ / 18
* **Frontend:** Bootstrap

---

## 💻 Настройка окружения разработчика (Локально)

Если вы хотите развернуть проект без Docker для разработки:

### 1. Клонирование и виртуальное окружение

```bash
git clone [https://github.com/Lecry1/corporate-market.git](https://github.com/Lecry1/corporate-market.git)
cd corporate-market

# Создание виртуального окружения
python -m venv .venv

# Активация (Linux/macOS)
source .venv/bin/activate
# Активация (Windows PowerShell)
.venv\Scripts\Activate.ps1

```

### 2. Установка зависимостей и Git hooks

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Установка pre-commit для автопроверки кода перед коммитом
pre-commit install
# Запуск ручной проверки
pre-commit run --all-files

```

### 3. Переменные окружения

Создайте файл `.env` в корне проекта на основе `.env.example`:

```env
SECRET_KEY=your_secret_key
DEBUG=True

DB_NAME=corporate_market
DB_USER=corpmarket_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

```

*Для генерации нового `SECRET_KEY` используйте команду:*

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🧪 Тестирование и работа с БД

При запущенном контейнере можно накатить тестовые данные или сделать бэкап.

**Создание дампа текущей базы данных:**

```bash
./fixture_backup.sh  
```

**Тестовые аккаунты (доступны после загрузки фикстур):**

* `admin@admin.com` / Пароль: `admin` (Admin)
* `qwerty@qwerty.com` / Пароль: `123qweasdzxc!`
* `mikle@milke.com` / Пароль: `123qweasdzxc!`

### Покрытие кода (Coverage)

Запуск тестов и генерация HTML-отчета:

```bash
docker compose exec web pip install coverage
docker compose exec web sh -c "cd CorpMarket && coverage run manage.py test && coverage html"

```

Отчет будет доступен в файле: `CorpMarket/htmlcov/index.html`

---

## 🏗 Архитектура и структура базы данных

* **Users:** Основная пользовательская сущность (фото, адрес, рейтинги продавца/покупателя).
* **Credentials:** Данные для входа (`OneToOne` к `Users`, логин, хеш пароля).
* **Admin:** Права администратора (`OneToOne` к `Users`).
* **Adverts:** Основная сущность объявлений (статус, категория, цена, описание, адрес).
* **Photos:** Фотографии, прикрепленные к объявлениям (`ForeignKey` к `Adverts`).
* **Chats:** Диалоги между автором объявления и покупателем.
* **Messages:** Сообщения внутри чата.
* **Reviews:** Отзывы по завершённым сделкам (оценка, текст, кому оставлен).

**Связи:**

* *Users → Adverts / Reviews / Chats / Messages* (1:M)
* *Adverts → Photos / Reviews / Chats* (1:M)
* *Chats → Messages* (1:M)
* *Users → Credentials / Admin* (1:1)

**ER-диаграмма:**
![image 20](./docs/images/image_20.png)
---

**Схема сервисов:**
<img width="1061" height="391" alt="Схема Сервисов" src="https://github.com/user-attachments/assets/bc31bc04-f6c5-4ebb-96f6-107e759e6262" />
---

## 📸 Скриншоты интерфейса

- **Авторизация и Регистрация**
![image 2](./docs/images/image_2.png)
![image 3](./docs/images/image_3.png)

- **Детальный просмотр объявления**
![image 5](./docs/images/image_5.png)

- **Список объявлений** 
![image 15](./docs/images/image_15.png)

- **Просмотр профиля**
![image 18](./docs/images/image_18.png)

- **Чаты**
<img width="1668" height="1030" alt="image" src="https://github.com/user-attachments/assets/9c0fe0b6-c1ab-42e5-a50a-3ef9c9f948c2" />

- **Админка**

Администратор имеет возможность удаления и редактирования чужих объявлений
<img width="1147" height="472" alt="image" src="https://github.com/user-attachments/assets/91b51016-040b-46a7-9cad-2c8e14c4cc16" />

- **Отзывы** 
![image 22](./docs/images/image_22.png)

---

## 👥 Разработчики

Проект выполняли:

* **Глебов Владислав Сергеевич**
* Лямин Егор Алексеевич
* Соколов Сергей Константинович
* Дашкин Рушан Ряшидович
* Гущин Александр Сергеевич
