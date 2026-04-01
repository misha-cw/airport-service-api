
# Airport Service API

## Overview
A Django REST Framework (DRF) based API for managing airport operations and services.

## Features
- JWT authenticated
- Documentation is located at /api/doc/swagger/
- Admin panel /admin/
- Managing orders and tickets
- Creating flighs, crew, routes, airports, airplanes and airplane types
- Filtering for routes and fligths

## Installing using GitHub

Install PostgresSQL and create db

### Setup
```bash
git clone <https://github.com/misha-cw/airport-service-api.git>
cd airport-service-api
python -m venv .venv
source .venv/biv/activate  #Windows: .venv\Scripts\activate
pip install -r requirements.txt
set DB_HOST=<your db hostname>
set DB_NAME=<your db name>
set DB_USER=<your db username>
set DB_PASSWORD=<your db user password>
set SECRET_KEY=<your secret key>
python manage.py migrate
python manage.py runserver
```

### Run with Docker

Docker should be installed

```bash
docker-compose build
docker-compose up
```

## Getting access
- Create user via /api/user/register/
- Get access token via /api/user/token/
