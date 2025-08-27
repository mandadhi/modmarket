# modmarket

[![Build Status](https://img.shields.io/github/actions/workflow/status/mandadhi/modmarket/main.yml?branch=main)]()

## Table of Contents

1.  [Description](#description)
2.  [Features](#features)
3.  [Tech Stack](#tech-stack)
4.  [File Structure Overview](#file-structure-overview)
5.  [Prerequisites](#prerequisites)
6.  [Installation](#installation)
7.  [Usage / Getting Started](#usage--getting-started)
8.  [Database Configuration](#-database-configuration)
9.  [Contact](#contact)

## Description

A web application built with Django, utilizing MongoDB and PostgreSQL for database management. Deployed online at https://modmarket-production.up.railway.app/.
<!-- TODO: Add screenshots if applicable -->

## ✨ Features

### 👤 User Features
- User authentication (signup, login, logout)
- Password reset & change password
- Save/bookmark mods
- comment on mods
- User history (recently viewed/downloaded mods)

### 📦 Mod / Product Features
- Upload mods with file & media support
- Browse mods by categories
- Search & filter mods (category, popularity, rating, etc.)
- Detailed mod pages with description, screenshots & reviews
- Download option with stats
- Product status display (active, inactive, moderation pending)

### 🗂 Marketplace & Categories
- Dynamic categories (from MongoDB collections)
- Preferred vs non-preferred categories (based on user profile)
- Trending & popular mods section
- Review system for mods

### 🔧 Admin & Moderation
- Custom admin dashboard (staff-only access)
- Approve/reject mods (moderation system)
- Developer management (create or link dev profiles)
- Stats dashboard (users, mods, reviews, categories)

### 🛠 Tech Stack
- **Backend:** Django
- **Database:** MongoDB  
- **Frontend:** Django Templates + Tailwind CSS  
- **Storage:** Supabase / Railway / Cloud storage for media  
- **Static Files:** Whitenoise for deployment  

### 🌍 Deployment
- Deployed on **Railway** with free subdomain
- Supports **custom domain** with HTTPS (SSL auto-managed)
- Environment variables managed using `.env` & `django-environ`


## Tech Stack

*   Python (Django Framework)
*   HTML
*   MongoDB
*   PostgreSQL

## File Structure Overview

```text
.
├── .gitignore
├── .hintrc
├── Procfile
├── manage.py
├── marketplace/
├── modmarket/
├── requirements.txt
├── runtime.txt
└── templates/
```

## Prerequisites

*   Python 3.x
*   pip (Python package installer)
*   MongoDB installed and running
*   PostgreSQL installed and running

## Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/mandadhi/modmarket.git
    cd modmarket
    ```

2.  Create a virtual environment (recommended):

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate  # On Windows
    ```

3.  Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage / Getting Started

1.  Configure the database settings (see Configuration section).

2.  Run database migrations:

    ```bash
    python manage.py migrate
    ```

3.  Create a superuser (admin account):

    ```bash
    python manage.py createsuperuser
    ```

4.  Start the Django development server:

    ```bash
    python manage.py runserver
    ```


## ⚙️ Database Configuration

### 1. Relational Database (SQLite / PostgreSQL)
- By default, the project uses **SQLite** for local development:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

For production, you can use PostgreSQL by setting the DATABASE_URL environment variable:

if not DEBUG:
    DATABASE_URL = env("DATABASE_URL", default=None)
    if DATABASE_URL:
        DATABASES["default"] = dj_database_url.config(default=DATABASE_URL)

### 2.MongoDB is used to store products, categories, developers, and reviews.
Set environment variables in .env or on your server:

from pymongo import MongoClient
def get_mongo_db():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB_NAME]

## Contact

**Harsha Vardhan Reddy**  
- Deployed Link: [https://modmarket-production.up.railway.app](https://modmarket-production.up.railway.app/)  
- Email: [harshavardhanreddy1715@gmail.com](mailto:harshavardhanreddy1715@gmail.com)
