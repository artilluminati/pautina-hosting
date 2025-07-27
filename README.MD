**Установка проекта**

**Требования**

Необходимо установить вручную, если не установлено

-   Python 3.12+
-   Poetry (менеджер пакетов для Python) - можно обойтись и без него, тогда нужно все зависимости из `pyproject.toml` установить глобально через `pip install [список пакетов]`
-   PostgreSQL (база данных)

**Шаг 1: Установка Poetry**

Установите Poetry любым удобным способом, следуя инструкциям на официальном сайте: https://python-poetry.org/docs/#installation

(Не забудьте прописать в [PATH](<https://ru.wikipedia.org/wiki/PATH_(%D0%BF%D0%B5%D1%80%D0%B5%D0%BC%D0%B5%D0%BD%D0%BD%D0%B0%D1%8F)>) все необходимые переменные)

**Шаг 2: Клонирование репозитория**

Клонировать репозиторий проекта:

```bash
git clone https://github.com/artilluminati/pautina-hosting
```

**Шаг 3: Установка зависимостей**

Перейдите в папку бэкенда и установите зависимости:

```bash
cd backend
poetry install
```

**Шаг 4: Настройка базы данных**

_(Пункт в разработке)_

Создайте базу данных PostgreSQL и пользователя с необходимыми правами. Затем, создайте файл `.env` в корне проекта с переменными окружения:

```makefile
DATABASE_URL=postgresql://user:password@localhost:5432/webhosting
SECRET_KEY=supersecretkey
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
TEST_EMAIL=user@example.com
TEST_PASSWORD=user123
```

**Шаг 5: Запуск миграций**

_(Пункт в разработке)_

Запустите миграции для создания таблиц в базе данных:

```bash
poetry run alembic upgrade head
```

**Шаг 6: Запуск сервера**

Запустите сервер, выполнив файл `main.py` в окружении, где установлены все необходимые зависимости:

```bash
python backend/main.py
```

**Шаг 7: Проверка**

Откройте веб-браузер и перейдите по адресу `http://localhost:8000`. Вы должны увидеть сообщение "Hello World".

**Шаг 8: Настройка frontend**

Перейдите в папку `frontend` и установите зависимости:

```bash
cd frontend
npm install
```

Запустите frontend:

```bash
npm run dev
```

Откройте веб-браузер и перейдите по адресу `http://localhost:5173`. Вы должны увидеть интерфейс приложения.

**Готово!**

Вы успешно установили проект. Теперь вы можете начать работать с приложением.
