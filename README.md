# Cafe manager

## Установка

### 1. Клонирование репозитория

```sh
git clone https://github.com/cojode/em-jan-cafe.git
```

Скопируйте и настройте .env файл:

```sh
cp .env.exanple .env
```

### 2. Локальный запуск

#### 2.1 Установите зависимости

С помощью [Poetry](https://python-poetry.org/docs/#installation)

```sh
poetry install
poetry shell
```

С помощью pip:

```sh
python -m venv venv
source venv/bin/activate 
pip install -r requirements.txt
```

#### 2.2 Настройка базы данных

```sh
cd cafe_manager
python manage.py migrate
```

Загрузите фикстуру с блюдами ```cafe_manager/orders/fixtures/example_dishes.json```

```sh
python manage.py loaddata example_dishes
```

#### 2.3 Запуск сервера

```sh
python manage.py runserver
```

### 3 Запуск внутри контейнера

Убедитесь что находитесь в корне проекта:

```sh
docker compose up --build 
```

Остановить контейнер:

```sh
docker compose down
```

## API

Дополнительно реализуется REST API для взаимодействия с заказами.

### Примеры запросов

- **Получить список заказов**: `GET /api/orders/`

## Тестирование

### Запуск тестов

```sh
```

## Структура проекта
