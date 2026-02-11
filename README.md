# Sensor Community Analytics

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-3.2%2B-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Ask DeepWiki](https://devin.ai/assets/askdeepwiki.png)](https://deepwiki.com/techcolab-org/sensor-community-analytics)
<!-- [TODO: Add CI/CD badge once GitHub Actions workflow is set up] -->
<!-- [TODO: Add code coverage badge] -->
<!-- [TODO: Add PyPI badge if package is published] -->

> A comprehensive Django-based web application for managing, downloading, and analyzing air quality data from the Sensor.Community network.

**Sensolog** streamlines the process of collecting and analyzing data from distributed environmental sensors. It provides a user-friendly interface to organize sensor stations, fetch historical data, and explore downloaded datasets—all within a single application. Perfect for individual station owners, researchers, and organizations managing multiple air quality monitoring sources.

---

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Standard Installation](#standard-installation)
  - [Docker Installation](#docker-installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Quick Start Guide](#quick-start-guide)
  - [Managing Stations](#managing-stations)
  - [Managing Sensors](#managing-sensors)
  - [Downloading Data](#downloading-data)
  - [Viewing and Analyzing Data](#viewing-and-analyzing-data)
- [Project Architecture](#project-architecture)
- [File Structure](#file-structure)
- [Data Schema](#data-schema)
- [Development](#development)
  - [Running Tests](#running-tests)
  - [Code Quality](#code-quality)
  - [Database Migrations](#database-migrations)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Maintainers](#maintainers)
- [Acknowledgments](#acknowledgments)
- [FAQ](#faq)

---

## Features

### Core Functionality

- **🗺️ Station & Sensor Management**
  - Add and organize monitoring stations with geographic details
  - Interactive maps powered by PostGIS and Leaflet.js
  - Attach and configure multiple sensor types per station
  - Geocoding support via Geopy

- **📥 Advanced Data Downloader**
  - Download sensor data for customizable date ranges
  - Bulk download for multiple stations simultaneously
  - Filter downloads by specific sensor IDs
  - Automatic retry logic for failed downloads

- **🔄 Automated Data Aggregation**
  - Merge daily CSV files into monthly datasets
  - Combine monthly files into yearly aggregates
  - Configurable merge strategies for data consolidation

- **📂 Integrated File Explorer**
  - Web-based file browser for downloaded sensor data
  - Hierarchical navigation (Station → Sensor → Date)
  - Visual folder inspection and file management

- **📊 In-App CSV Viewer**
  - Interactive, Excel-like table view for CSV files
  - Pagination for large datasets
  - Search and filter capabilities
  - Export options for processed data

- **📈 Interactive Dashboard**
  - Real-time station status monitoring
  - Latest sensor readings display
  - Visual analytics and data insights
  - Responsive design for mobile and desktop

- **🔍 Search & Discovery**
  - Global search modal for quick station lookup
  - Advanced filtering options
  - Detailed station information views

- **🔐 User Authentication**
  - Secure registration and login system
  - Role-based access control
  - User session management

---

## Demo

<!-- [TODO: Add screenshots or animated GIFs of key features] -->
<!-- [TODO: Add link to live demo instance if available] -->

---

## Technology Stack

### Backend
- **Python** (3.8+)
- **Django** (3.2+)
- **Django GIS** - Geospatial database support
- **PostgreSQL** with **PostGIS** extension

### Frontend
- **HTML5** & **CSS3**
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript** (ES6+)
- **Leaflet.js** - Interactive mapping
- **Font Awesome** - Icon library

### Data Processing
- **Pandas** - Data analysis and CSV manipulation
- **Requests** - HTTP library for API calls
- **Geopy** - Geocoding services

### Additional Libraries
- **django-environ** - Environment variable management
- **django-jazzmin** - Modern admin interface
- **psycopg2** - PostgreSQL adapter

---

## Prerequisites

Before installing Sensor Community Analytics, ensure you have the following:

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Docker** and **Docker Compose** (for PostgreSQL with PostGIS) ([Installation Guide](https://docs.docker.com/get-docker/))
- **pip** (Python package installer)
- **virtualenv** or **venv** (recommended)
- **Git** ([Download](https://git-scm.com/downloads))

### System Requirements

- **OS**: Linux, macOS, or Windows 10/11
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 10GB minimum for application and data storage
- **Network**: Internet connection for downloading sensor data

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/techcolab-org/sensor-community-analytics.git
cd sensor-community-analytics
```

### 2. Set Up PostgreSQL with PostGIS and nginx using Docker

Create a `docker-compose.yml` file in the project root:

```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:15-3.3
    container_name: sensolog_db
    environment:
      POSTGRES_DB: sensolog_db
      POSTGRES_USER: sensolog_user
      POSTGRES_PASSWORD: your_secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - sensolog_network

  nginx:
    image: nginx:alpine
    container_name: sensolog_nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./staticfiles:/var/www/html/{project_folder}/staticfiles:ro
      - ./mediafiles:/var/www/html/{project_folder}/mediafiles:ro
    depends_on:
      - db
    restart: unless-stopped
    networks:
      - sensolog_network

volumes:
  postgres_data:

networks:
  sensolog_network:
    driver: bridge
```

Create an `nginx.conf` file in the project root:

```nginx
server {
    listen 80;
    server_name {your_domain};
    client_max_body_size 20M;

    # ------------------------------
    # FAVICON
    # ------------------------------
    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    # ------------------------------
    # STATIC FILES
    # ------------------------------
    location /static/ {
        alias /var/www/html/{project_folder}/staticfiles/;
        access_log off;
        expires 30d;
    }

    # ------------------------------
    # MEDIA FILES
    # ------------------------------
    location /media/ {
        alias /var/www/html/{project_folder}/mediafiles/;
        access_log off;
        expires 30d;
    }

    # ------------------------------
    # DJANGO (ALL OTHER ROUTES)
    # ------------------------------
    location / {
        proxy_pass http://host.docker.internal:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # TIMEOUT SETTINGS FOR LONG DOWNLOADS
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;

        # Disable buffering for streaming responses
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
```

Start the Docker containers:

```bash
docker-compose up -d
```

Verify the services are running:

```bash
docker-compose ps
```

You should see both `sensolog_db` and `sensolog_nginx` running.

### 3. Create and Activate Virtual Environment

**Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy the sample environment file:

```bash
cp env-sample .env
```

Edit `.env` with your configuration (see [Configuration](#configuration) section for details):

**Note**: _{your_domain}_ should be same as nginx config file domain name
```ini
# Application Settings
DEBUG=True
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ALLOWED_HOSTS=127.0.0.1,localhost,{your_domain}

# Database Configuration (matches docker-compose.yml)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sensolog_db
DB_USER=sensolog_user
DB_PASS=your_secure_password

```

### 6. Run Database Migrations

```bash
python manage.py migrate
```

### 7. Load Initial Data

Load predefined sensor types:

```bash
python manage.py load_sensor_type
```

### 8. Create Admin User

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

### 9. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 10. Start Development Server

```bash
python manage.py runserver
```

The application is now available at **http://127.0.0.1:8000**

---

## Configuration

### Environment Variables

The application uses environment variables for configuration. All settings are defined in the `.env` file.

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (use long random string) | `django-insecure-abc123...` |
| `DB_NAME` | PostgreSQL database name | `sensolog_db` |
| `DB_USER` | Database username | `sensolog_user` |
| `DB_PASS` | Database password | `SecureP@ssw0rd` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode (disable in production) | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` |
| `LANGUAGE_CODE` | Application language | `en-us` |
| `TIME_ZONE` | Application timezone | `UTC` |
| `STATIC_URL` | URL for static files | `/static/` |
| `MEDIA_URL` | URL for media files | `/media/` |

### Generating a Secret Key

Generate a secure secret key using Python:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use this one-liner:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Sample .env File

```ini
# Application Settings
DEBUG=True
SECRET_KEY=django-insecure-your-unique-secret-key-change-this
ALLOWED_HOSTS=127.0.0.1,localhost,yourdomain.com

# PostgreSQL Database with PostGIS
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sensolog_db
DB_USER=sensolog_user
DB_PASS=your_database_password

```

---

## Usage

### Quick Start Guide

Once installed, follow these steps to start using Sensor Community Analytics:

1. **Access the Application**: 
   - Development server: http://127.0.0.1:8000
   - Via nginx (if using Docker Compose): http://localhost or http://sensolog.local
2. **Log In**: Use the superuser credentials you created
3. **Add Your First Station**: Click "Add Station" on the dashboard
4. **Configure Sensors**: Add sensors to your station using Sensor.Community IDs
5. **Download Data**: Select date range and download historical data
6. **Explore Data**: Use the file browser and CSV viewer to analyze results

### Managing Stations

#### Adding a Station

1. Click the **"Add Station"** button on the main dashboard
2. Fill in the station details:
   - **Station Name**: Descriptive name for your monitoring location
   - **Latitude**: Geographic latitude (e.g., 40.7128)
   - **Longitude**: Geographic longitude (e.g., -74.0060)
   - **Address** (optional): Physical address
   - **Description** (optional): Additional notes
3. Click **"Save"** to create the station

**Example via Django Shell:**

```python
from sensor.models import Station

station = Station.objects.create(
    name="Downtown Monitoring Station",
    latitude=40.7128,
    longitude=-74.0060,
    address="123 Main St, New York, NY 10001",
    description="Air quality monitoring in downtown area"
)
```

#### Viewing Station Details

- Click on any station card to view detailed information
- Interactive map shows exact location
- View all attached sensors and their status
- Access download history and data files

### Managing Sensors

#### Adding a Sensor to a Station

1. Navigate to the desired station
2. Click the **"+ Sensor"** button
3. Enter the **Sensor ID** from Sensor.Community
   - The system will attempt to auto-populate sensor type and metadata
   - If unknown, manually select the sensor type
4. Configure additional settings (if applicable)
5. Click **"Save"**

**Supported Sensor Types:**

<!-- [TODO: List all supported sensor types from load_sensor_type command] -->
- SDS011 (PM2.5, PM10)
- DHT22 (Temperature, Humidity)
- BME280 (Temperature, Humidity, Pressure)
- Additional types loaded via `load_sensor_type` command

**Example via Django Shell:**

```python
from sensor.models import Station, Sensor, SensorType
from core.models import CoreSensorType

station = Station.objects.get(name="Downtown Monitoring Station")
sensor_type_exists = SensorType.objects.filter(name="SDS011").exists()

if sensor_type_exists:
    sensor_type = SensorType.objects.get(name="SDS011")
else:
    core_sensor_type = CoreSensorType.objects.get(name="SDS011")
    sensor_type = SensorType.objects.create(
        name=core_sensor_type.name,
        description=core_sensor_type.description
    )

sensor = Sensor.objects.create(
    station=station,
    sensor_id="12345",
    sensor_type=sensor_type,
    is_active=True
)
```

### Downloading Data

#### Download Options

**Option 1: Station-Level Download**
1. Check the checkbox on one or more station cards
2. Click the **"Download Data"** button (top of page or on station card)
3. After click the button, Download Dialog box will pop up
4. Set Date Range or select today, 7days, 30days or last year date
5. Leave Merge Options as it is [To merge data according to month and year]
6. **Note**: _Download Location is reference to how the downloaded files looks like_
7. Click the **Start Download** button to start downloading

**Option 2: Sensor-Level Download**
1. Expand a station's sensor list
2. Check specific sensors you want to download
3. Click **"Download Data"** button
4. After click the button, process is same as option 1 above [From point 4] 

#### Download Configuration

In the download modal:
- **Start Date**: Beginning of date range
- **End Date**: End of date range (inclusive)
- **Merge Daily Files**: Combine daily CSVs into monthly files
- **Merge Monthly Files**: Combine monthly CSVs into yearly files

#### Download Process

```bash
# Data is saved to:
sensor_data_by_station/
├── StationName_UniqueID/
│   ├── sensor_12345/
│   │   ├── 2024-01/
│   │   │   ├── 2024-01-01.csv
│   │   │   ├── 2024-01-02.csv
│   │   │   └── ...
│   │   ├── 2024-02/
│   │   └── merged/
│   │       ├── 2024-01_merged.csv
│   │       └── 2024_yearly.csv
```

**Programmatic Download:**

```python
from community_sensor.station_data_downloader import StationDataDownloader

# Download data for specific sensor
downloader = StationDataDownloader(
    station_id=1,
) # Go to station_data_downloader.py inside community_sensor to check how it works

downloader.download_specific_sensor(
    sensor_id=12345, # Sensor Id from devices.sensor.community that has been added in this app
    start_date="2024-01-01",
    end_date="2024-01-31",
)
```

### Viewing and Analyzing Data

#### File Browser

1. Click **"View Station Data"** button (appears after first download)
2. Navigate the folder hierarchy:
   - Station folders
   - Sensor subfolders
   - Monthly data directories
   - Merged data files

#### CSV Viewer

1. Click on any `.csv` file in the file browser
2. Interactive table displays with:
   - **Pagination**: Navigate large datasets
   - **Search**: Filter rows by keyword
   - **Sort**: Click column headers to sort
   - **Export**: Download filtered/sorted results

**CSV Data Structure:**

Typical sensor CSV contains:
- `timestamp`: ISO 8601 datetime
- `sensor_id`: Unique sensor identifier
- `sensor_type`: Type of measurement
- `location`: Geographic coordinates
- `P1`: PM10 particulate matter (μg/m³)
- `P2`: PM2.5 particulate matter (μg/m³)
- Additional fields depending on sensor type

---

### Management Commands

#### load_sensor_type

Load predefined sensor types into the database.

```bash
python manage.py load_sensor_type
```

**Description:** Populates the `SensorType` model with standard sensor configurations from preset json file.

<!-- [TODO: Add additional custom management commands if they exist] -->

### Utility Functions

#### Data Download Utilities

**Location:** `sensor/get_sensor_data.py`

```python
# Example usage
from sensor.get_sensor_data import GetSensorData

# Example with optimized parallel downloads
downloader = GetSensorData(output_dir='sensor_data', max_workers=20)

# Set date range
downloader.set_date_range('2024-01-01', '2024-12-31')

# Download with parallel processing
result = downloader.download_from_date(
    sensor_id='95522',
    sensor_type='sds011',
    merge=True,
    create_missing=True,
    auto_fetch_metadata=True,
    merge_by_year=True
)
```
---

## Project Architecture

### Application Structure

Sensor Community Analytics follows Django's MTV (Model-Template-View) architecture:

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Browser    │─────▶│  Django View │─────▶│   Model     │
│  (Client)   │◀─────│  (Logic)     │◀─────│ (Database)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Template    │
                     │  (HTML)      │
                     └──────────────┘
```

### Component Overview

- **sensolog/**: Project configuration and routing
- **core/**: Authentication, User Registration
- **sensor/**: Station and sensor management (primary app)
- **community_sensor/**: Data download, file browser, CSV viewer
- **templates/**: HTML templates with Tailwind CSS
- **static/**: JavaScript, CSS, images, and other assets

### Data Flow

1. **User Action** → User interacts with dashboard or forms
2. **View Processing** → Django view validates and processes request
3. **API Integration** → System calls Sensor.Community API if needed
4. **Data Storage** → CSV files saved to `sensor_data_by_station/`
5. **Database Update** → Metadata stored in PostgreSQL/PostGIS
6. **Response** → Updated view rendered and returned to user

### External Dependencies

- **Sensor.Community API**: Source of sensor data
  - API Base URL: `https://archive.sensor.community/`
  
- **PostGIS**: Spatial database for geographic queries
- **Geocoding Services**: Via Geopy (Google Maps, Nominatim, etc.)

---

## File Structure

```
sensor-community-analytics/
├── sensolog/                   # Django project configuration
│   ├── __init__.py
│   ├── settings.py            # Main settings file
│   ├── urls.py                # Root URL configuration
│   ├── wsgi.py                # WSGI application entry point
│   └── asgi.py                # ASGI application entry point
├── core/                       # Core app for shared functionality
│   ├── models.py              # Base models and mixins
│   ├── views.py               # Authentication views
│   ├── admin.py               # Admin customizations
│   └── utils.py               # Shared utility functions
├── sensor/                     # Main sensor management app
│   ├── models.py              # Station, Sensor, SensorType models
│   ├── views.py               # Station/sensor CRUD views
│   ├── urls.py                # App-specific URL routing
│   ├── forms.py               # Django forms for data entry
│   ├── admin.py               # Admin interface config
│   ├── management/
│   │   └── commands/
│   │       └── load_sensor_type.py  # Custom management command
│   └── migrations/            # Database migrations
├── community_sensor/           # Data download and browsing app
│   ├── models.py              # Download history models
│   ├── views.py               # File browser, CSV viewer, download views
│   ├── urls.py                # Download and viewer URLs
│   ├── utils.py               # Download and merge utilities
│   └── templates/             # App-specific templates
├── accounts/                   # User authentication app
│   ├── models.py              # Custom user model (if any)
│   ├── views.py               # Registration, login views
│   ├── forms.py               # User registration forms
│   └── urls.py                # Auth-related URLs
├── templates/                  # Global HTML templates
│   ├── base.html              # Base template with common layout
│   ├── dashboard.html         # Main dashboard
│   ├── station_detail.html    # Station details view
│   ├── file_browser.html      # File explorer interface
│   ├── csv_viewer.html        # CSV table viewer
│   └── auth/                  # Authentication templates
│       ├── login.html
│       └── register.html
├── static/                     # Static assets
│   ├── css/
│   │   └── custom.css         # Custom stylesheets
│   ├── js/
│   │   ├── dashboard.js       # Dashboard interactions
│   │   ├── maps.js            # Leaflet map configurations
│   │   └── file_browser.js    # File browser functionality
│   └── images/                # Image assets
├── staticfiles/                # Collected static files (generated)
├── mediafiles/                 # User-uploaded media files
├── media/                      # User-uploaded files (if any)
├── sensor_data_by_station/     # Downloaded sensor data (not in git)
├── docker-compose.yml          # Docker services configuration (PostgreSQL + nginx)
├── nginx.conf                  # nginx reverse proxy configuration
├── requirements.txt            # Python dependencies
├── manage.py                   # Django management script
├── env-sample                  # Environment variable template
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
└── LICENSE                     # License file
```

---

## Development

### Setting Up Development Environment

1. Follow standard installation steps
2. Enable DEBUG mode in `.env`:

```ini
DEBUG=True
```

### Database Migrations

**Creating migrations after model changes:**

```bash
python manage.py makemigrations
```

**Applying migrations:**

```bash
python manage.py migrate
```

**Viewing migration status:**

```bash
python manage.py showmigrations
```

**Rolling back migrations:**

```bash
python manage.py migrate sensor 0003  # Migrate to specific migration
```

### Django Admin

Access the admin interface at http://127.0.0.1:8000/admin/

The admin uses **django-jazzmin** for a modern UI. Customize admin settings in `sensolog/settings_jazzmin.py`:

**Note**: Take reference from https://django-jazzmin.readthedocs.io/

```python
JAZZMIN_SETTINGS = {
    "site_title": "Sensolog Admin",
    "site_header": "Sensor Community Analytics",
    # ... additional settings
}
```

---

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use environment variables for all secrets
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up HTTPS/SSL certificates (update nginx.conf for SSL)
- [ ] Use production database (PostgreSQL with PostGIS via Docker)
- [ ] Configure static file serving (nginx in Docker)
- [ ] Set up proper logging
- [ ] Enable database backups
- [ ] Set up monitoring (Sentry, New Relic, etc.)
- [ ] Configure systemd service for Gunicorn

### Deployment with Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run application
gunicorn sensolog.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Using Docker Compose for Production

The included `docker-compose.yml` provides both PostgreSQL and nginx services. For production:

1. **Update nginx.conf** for your domain:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    # ... rest of the configuration
}
```

2. **For HTTPS/SSL**, update nginx.conf:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... rest of the configuration
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

3. **Mount SSL certificates** in docker-compose.yml:
```yaml
nginx:
  volumes:
    - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    - ./staticfiles:/var/www/html/Sensolog/staticfiles:ro
    - ./mediafiles:/var/www/html/Sensolog/mediafiles:ro
    - /path/to/ssl/certs:/etc/nginx/ssl:ro
```

4. **Start services**:
```bash
docker-compose up -d
```

### Production Environment Variables

Create a `.env` file for production with the following settings:

```ini
DEBUG=False
SECRET_KEY=use-a-very-long-random-string-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,sensolog.local

# Production database (via Docker)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sensolog_production
DB_USER=sensolog_prod_user
DB_PASS=very_secure_password_here
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Docker Services Not Starting

**Error:** Services fail to start or containers keep restarting

**Solution:**
```bash
# Check status of all services
docker-compose ps

# View logs for specific service
docker-compose logs db
docker-compose logs nginx

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

#### 2. Database Connection Error

**Error:** `django.db.utils.OperationalError: could not connect to server`

**Solution:**
- Verify PostgreSQL Docker container is running: `docker-compose ps`
- Start the database if not running: `docker-compose up -d`
- Check database credentials in `.env` match those in `docker-compose.yml`
- Verify port 5432 is not being used by another service: `sudo lsof -i :5432`
- Check Docker logs: `docker-compose logs db`

#### 3. nginx Cannot Access Django Application

**Error:** nginx shows "502 Bad Gateway" or connection errors

**Solution:**
- Ensure Django development server is running on port 8000
- For Docker on Linux, use `172.17.0.1:8000` instead of `host.docker.internal:8000` in nginx.conf
- Check if Django is accessible: `curl http://127.0.0.1:8000`
- Restart nginx container: `docker-compose restart nginx`

#### 4. Static Files Not Loading Through nginx

**Error:** CSS/JS files return 404 through nginx

**Solution:**
```bash
# Ensure static files are collected
python manage.py collectstatic --noinput

# Verify staticfiles directory exists and has correct permissions
ls -la staticfiles/

# Check nginx container has access to static files
docker-compose exec nginx ls -la /var/www/html/Sensolog/staticfiles/

# Restart nginx
docker-compose restart nginx
```

#### 5. PostGIS Extension Not Found

**Error:** `django.core.exceptions.ImproperlyConfigured: Cannot use GeoDjango without PostGIS`

**Solution:**

If using Docker (recommended):
```bash
# Ensure the PostGIS container is running
docker-compose ps

# The postgis/postgis image includes PostGIS by default
# Verify by connecting to the container
docker-compose exec db psql -U sensolog_user -d sensolog_db -c "SELECT PostGIS_version();"
```

If installed manually:
```sql
-- Connect to your database
\c sensolog_db

-- Install PostGIS
CREATE EXTENSION postgis;

-- Verify installation
SELECT PostGIS_version();
```

#### 6. Missing Environment Variables

**Error:** `KeyError: 'SECRET_KEY'`

**Solution:**
- Ensure `.env` file exists in project root
- Verify all required variables are set
- Check `.env` file syntax (no quotes unless needed, no spaces around `=`)

#### 7. Sensor Data Download Fails

**Error:** Download hangs or returns empty files

**Solution:**
- Verify internet connectivity
- Check Sensor.Community API status: https://archive.sensor.community/
- Ensure sensor ID exists and is active
- Check date range (data may not exist for future dates)
- Review logs for API rate limiting

#### 8. Migration Conflicts

**Error:** `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solution:**
```bash
# View current migration status
python manage.py showmigrations

# If safe to reset (development only - backs up data first)
python manage.py dumpdata > backup.json
python manage.py migrate --fake sensor zero
python manage.py migrate sensor

# Or fix conflicts manually by editing migration dependencies
```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs**: Review Django logs and browser console
2. **Search Issues**: Check [GitHub Issues](https://github.com/techcolab-org/sensor-community-analytics/issues)
3. **Ask Questions**: Open a new issue with:
   - Django version
   - Python version
   - Error message and full traceback
   - Steps to reproduce

---

## Contributing

We welcome contributions! Here's how you can help:

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Write or update tests**
5. **Ensure all tests pass**: `python manage.py test`
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guide for Python code
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed
- Keep pull requests focused on a single feature/fix

### Code Review Process

1. Maintainers will review your PR within 1-2 weeks
2. Address any requested changes
3. Once approved, maintainers will merge your PR

### Areas for Contribution

- 🐛 **Bug Fixes**: Check open issues labeled "bug"
- ✨ **New Features**: Propose features via GitHub Issues first
- 📚 **Documentation**: Improve README, add code comments, create tutorials
- 🧪 **Testing**: Increase code coverage
- 🌍 **Internationalization**: Add translations
- ♿ **Accessibility**: Improve UI accessibility

<!-- [TODO: Create CONTRIBUTING.md with detailed guidelines] -->

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

<!-- [TODO: Verify license type and add LICENSE file if missing] -->

**Summary:**
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ Liability and warranty disclaimer applies

---

## Maintainers

**TechColab Organization**
- GitHub: [@techcolab-org](https://github.com/techcolab-org)
- Repository: [sensor-community-analytics](https://github.com/techcolab-org/sensor-community-analytics)

<!-- [TODO: Add individual maintainer contacts] -->

### Contact

- **Issues & Bugs**: [GitHub Issues](https://github.com/techcolab-org/sensor-community-analytics/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/techcolab-org/sensor-community-analytics/discussions)
- **Email**: [TODO: Add contact email]

---

## Acknowledgments

- **Sensor.Community**: For providing open air quality data
- **Django Community**: For the excellent web framework
- **PostGIS**: For spatial database capabilities
- **Leaflet.js**: For interactive mapping
- **Contributors**: Thank you to all who have contributed to this project

### Related Projects

- [Sensor.Community](https://sensor.community/) - Open air quality data platform
- [Luftdaten.info](https://luftdaten.info/) - DIY sensor network
- [OpenAQ](https://openaq.org/) - Open air quality data aggregator

---

## FAQ

### General Questions

**Q: What is Sensor.Community?**  
A: Sensor.Community is a global network of citizen-operated air quality sensors. This application helps you download and analyze data from these sensors.

**Q: Do I need my own sensor to use this application?**  
A: No, you can analyze data from any public sensor on the Sensor.Community network.

**Q: Is this application free to use?**  
A: Yes, this is open-source software under the MIT license.

### Technical Questions

**Q: Which Python version is required?**  
A: Python 3.8 or higher is required.

**Q: Can I use SQLite instead of PostgreSQL?**  
A: While Django supports SQLite, PostGIS (required for geographic features) only works with PostgreSQL. We strongly recommend PostgreSQL.

**Q: How much disk space do I need?**  
A: This depends on how much data you download. A single sensor generates ~500MB per year. Plan for at least 10GB for the application and data storage.

**Q: Can I host this on a shared hosting service?**  
A: Shared hosting typically doesn't support Django applications with PostGIS. Use a VPS, cloud platform (AWS, Google Cloud, DigitalOcean), or PaaS (Heroku, PythonAnywhere).

**Q: How often is sensor data updated?**  
A: Sensor.Community archives data daily. You can schedule periodic downloads using cron or Django-Q.

### Data Questions

**Q: What data format is used?**  
A: Data is stored in CSV format with standardized columns.

**Q: Can I export data to other formats?**  
A: Currently, data is available in CSV. Future versions may support JSON, Excel, and database export.

**Q: How far back does historical data go?**  
A: This depends on the sensor. Some sensors have data going back to 2015.

---

## What's Next

### Planned Features

- [ ] **Data Visualization**: Built-in charts and graphs using Plotly or Chart.js
- [ ] **API Endpoints**: RESTful API for programmatic access
- [ ] **Scheduled Downloads**: Automatic periodic data downloads
- [ ] **Data Export**: Export to JSON
- [ ] **Email Notifications**: Alerts for data quality issues or download completions
- [ ] **Multi-language Support**: Internationalization (i18n)
- [ ] **Mobile App**: Companion mobile application
- [ ] **Advanced Analytics**: Statistical analysis and machine learning integration

### Roadmap

**Version 2.0** (Q2 2026)
- RESTful API
- Real-time data visualization
- Scheduled downloads

**Version 3.0** (TBD)
- Machine learning integration
- Predictive analytics
- Advanced reporting

### How You Can Help

Vote on features or suggest new ones in [GitHub Discussions](https://github.com/techcolab-org/sensor-community-analytics/discussions).

---

## Support

### Getting Support

- 📖 **Documentation**: You're reading it!
- 💬 **Community**: [GitHub Discussions](https://github.com/techcolab-org/sensor-community-analytics/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/techcolab-org/sensor-community-analytics/issues)
- 📧 **Email**: [Send email](mailto:asbn2231@gmail.com)

### Commercial Support

<!-- [TODO: Add commercial support information if available] -->

---

**Made with ❤️ by the Techcolab Community**

*Star ⭐ this repository if you find it useful!*