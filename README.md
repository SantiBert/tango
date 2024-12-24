# PomJuice backend

This repo contains the Rest API for Pom Juice application.

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

## Environment Setup

### Creating a Virtual Environment

It's recommended to use a virtual environment to manage project dependencies. This helps to isolate the project's dependencies from other projects.

#### Using virtualenv

If you haven't installed virtualenv, you can install it using pip:

```bash
pip install virtualenv
```
On Windows:

```bash
venv\Scripts\activate
```

On macOS and Linux:

```bash
source venv/bin/activate
```

#### Using virtualenv

```bash
pip install -r requirements.txt
```

## Start the app

1. Execute the command
```bash
python3 manage.py migrate
```
2. Load cities
```bash
python3 manage.py cities_light
```
3. Load Categories and Subcategories
```bash
python3 manage.py load_categories
```
4. Load Investors 
```bash
python3 manage.py load_investors
```

5. Load test users 
```bash
python3 manage.py load_users
```
6. Load startups 
```bash
python3 manage.py load_startups
```

## Run the tests

1. Execute the command "pytest"
```bash
pytest
```
