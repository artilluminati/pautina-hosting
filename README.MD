# Pautina Hosting

## Установка проекта

#### Требования

Убедитесь, что у вас установлены:

-   Python 3.12+
-   PostgreSQL
-   [Poetry](https://python-poetry.org/docs/#installation) — менеджер зависимостей (можно обойтись и без него, установив зависимости вручную из `pyproject.toml` через `pip`)

---

#### Шаг 1: Установка Poetry

Установите Poetry с сайта: https://python-poetry.org/docs/#installation

_Не забудьте прописать переменные окружения в `PATH`, если потребуется._

---

#### Шаг 2: Клонирование репозитория

```bash
git clone https://github.com/artilluminati/pautina-hosting
cd pautina-hosting/backend
```

---

#### Шаг 3: Установка зависимостей

```bash
poetry install
```

---

#### Шаг 4: Настройка базы данных

Создайте PostgreSQL-базу и пользователя. Затем в корне `backend/` создайте файл `.env`. Пример:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=supersecretkey
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
TEST_EMAIL=user@example.com
TEST_PASSWORD=user123
```

---

#### Шаг 5: Применение миграций

(В разработке, не тестировалось)

```bash
poetry run alembic upgrade head
```

---

#### Шаг 6: Запуск сервера

```bash
poetry run python src/app/main.py
```

Перейдите в браузере по адресу: [http://localhost:8000/health](http://localhost:8000/health) - должно отобразиться `{"status":"ok"}`

---

#### Шаг 7: Настройка frontend

```bash
cd ../frontend
npm install
npm run dev
```

Фронтенд доступен по адресу: [http://localhost:5173](http://localhost:5173)

---

**Готово!**
Вы успешно установили и запустили проект. Теперь можно работать с приложением.

---

## Документация

Для изучения автогенерируемой документации по бэкенду, откройте в браузере:

[backend/docs/\_build/html/app.html](backend/docs/_build/html/app.html)

Документация по API (В разработке) доступна на [данной странице](backend/docs/_build/html/app.routers.html)

---

Сборка документации (при её обновлении)

```bash
cd backend
sphinx-apidoc -o docs src/app
cd docs
./make html
```
