# Vigilant

Vigilant is a subscription tracking application built with FastAPI, SQLAlchemy, Jinja2, and Tailwind CSS. It helps users track free trials, monitor upcoming renewal dates, and generate alerts before a subscription becomes chargeable.

The project supports two database modes:

- SQLite for simple local development with no extra setup
- MySQL for production-style deployments

## What It Does

- User registration and login with signed-cookie sessions
- Subscription and free-trial tracking
- Dashboard with counts, status badges, and estimated savings
- Background watcher process that finds expiring trials
- In-app notifications for upcoming trial endings
- Optional Google OAuth preparation and SMTP placeholders

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy
- Jinja2
- Tailwind CSS via CDN
- SQLite for local development
- MySQL for production-style deployments

## Project Layout

```text
vigilant/
|-- app/
|   |-- auth/
|   |   |-- hashing.py
|   |   |-- oauth.py
|   |   `-- session_manager.py
|   |-- core/
|   |   `-- config.py
|   |-- database/
|   |   `-- session.py
|   |-- models/
|   |   |-- notification.py
|   |   |-- subscription.py
|   |   `-- user.py
|   |-- routes/
|   |   |-- auth_routes.py
|   |   |-- dashboard_routes.py
|   |   `-- sub_routes.py
|   |-- schemas/
|   |   |-- subscription.py
|   |   `-- user.py
|   |-- services/
|   |   |-- notification_service.py
|   |   |-- subscription_service.py
|   |   `-- user_service.py
|   `-- main.py
|-- static/
|   |-- css/custom.css
|   `-- js/main.js
|-- templates/
|   |-- add_subscription.html
|   |-- base.html
|   |-- dashboard.html
|   |-- edit_subscription.html
|   |-- login.html
|   `-- register.html
|-- run_watcher.sh
|-- run_web.sh
|-- schema.sql
|-- watcher.py
`-- README.md
```

## Quick Start

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the environment

```bash
cp .env.example .env
```

For local development, keep:

```env
USE_SQLITE=true
SQLITE_PATH=vigilant_dev.db
```

### 4. Start the web app

```bash
./run_web.sh
```

### 5. Start the watcher in a second terminal

```bash
./run_watcher.sh
```

### 6. Open the app

Visit `http://localhost:8000`

## MySQL Setup

Use MySQL only if you want a production-style database setup.

### 1. Create the schema

```bash
mysql -u root -p < schema.sql
```

### 2. Update `.env`

Set these values:

```env
USE_SQLITE=false
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=vigilant_db
```

### 3. Start the project

```bash
./run_web.sh
./run_watcher.sh
```

## Run Scripts

The project includes two small launch scripts:

- `./run_web.sh` starts Uvicorn on `0.0.0.0:8000`
- `./run_watcher.sh` starts the background watcher process

You can override the host or port for the web server:

```bash
HOST=127.0.0.1 PORT=9000 ./run_web.sh
```

## Current Readiness

The base application is ready to publish and run as a normal web app with:

- local login and registration
- subscription tracking
- in-app watcher notifications
- SQLite local development
- MySQL production-style configuration

These features are not fully wired yet and should be treated as follow-up setup:

- real SMTP email sending
- Google OAuth login flow in the user-facing routes
- live browser push updates such as WebSockets or Server-Sent Events

## Configuration

Settings are loaded from `.env` through `pydantic-settings`.

### Core settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `Vigilant` | Application name |
| `APP_VERSION` | `1.0.0` | Application version |
| `DEBUG` | `true` in example | Enables debug logging |
| `SECRET_KEY` | required | Session signing key |

### Database settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `USE_SQLITE` | `true` | Switch between SQLite and MySQL |
| `SQLITE_PATH` | `vigilant_dev.db` | SQLite database file |
| `DB_HOST` | `127.0.0.1` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_USER` | `vigilant_user` | MySQL username |
| `DB_PASSWORD` | `vigilant_pass` | MySQL password |
| `DB_NAME` | `vigilant_db` | MySQL database name |

### Watcher settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `WATCHER_POLL_INTERVAL` | `60` | Seconds between watcher sweeps |
| `WATCHER_ALERT_DAYS` | `3` | Days before trial end to alert |

### Optional integrations

| Variable | Purpose |
| --- | --- |
| `GOOGLE_CLIENT_ID` | Google OAuth client id |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL |
| `SMTP_HOST` | SMTP host |
| `SMTP_PORT` | SMTP port |
| `SMTP_USER` | SMTP username |
| `SMTP_PASSWORD` | SMTP password |
| `EMAIL_FROM` | Sender address for alert emails |

## OAuth Setup Notes

Google OAuth is only prepared in the codebase right now. Before calling the project production-ready for Google login, you still need to:

1. Create a Google OAuth app in Google Cloud Console
2. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in `.env`
3. Register the callback URL in the Google OAuth app settings
4. Add or finish the login and callback routes if you want end users to sign in with Google from the UI

If you do not plan to use Google login yet, leave those variables empty and continue using the built-in email/password authentication.

## Email Sending Notes

Real email sending is not enabled yet. The current watcher creates in-app notifications, but SMTP delivery still needs to be implemented and configured.

To enable email later, you will need to:

1. Choose an email provider such as Mailgun, SendGrid, or Amazon SES
2. Verify your sending domain and configure SPF and DKIM
3. Fill in `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `EMAIL_FROM`
4. Replace the current email stub in `app/services/notification_service.py`
5. Call the real email sender from the watcher flow

## Watcher Behavior

`watcher.py` runs as a separate process and continuously scans for subscriptions that need attention.

During each sweep it:

1. Marks overdue subscriptions as `EXPIRED`
2. Finds subscriptions inside the alert window
3. Creates in-app notifications
4. Moves notified subscriptions forward so the same alert is not repeated every cycle

## Current Application Flow

- Unauthenticated users are redirected to `/auth/login`
- New users can register and are signed in immediately
- Authenticated users land on `/dashboard`
- Subscriptions can be added, edited, cancelled, or deleted
- The watcher updates statuses and creates notifications in the background

## Security Notes

- Passwords are hashed with `passlib` and `bcrypt`
- Sessions are stored in signed cookies using `itsdangerous`
- SQLAlchemy is used for database access
- OAuth and SMTP code paths are prepared but not fully wired into end-user flows

## Troubleshooting

### The app does not start

- Confirm the virtual environment exists at `.venv`
- Reinstall dependencies with `pip install -r requirements.txt`
- Check whether `.env` exists and has valid values

### MySQL connection errors

- Make sure `USE_SQLITE=false`
- Confirm MySQL is running
- Confirm the database credentials in `.env`
- Create the schema with `mysql -u root -p < schema.sql`

### The watcher is not creating alerts

- Make sure the watcher process is running in a separate terminal
- Check `WATCHER_ALERT_DAYS` in `.env`
- Confirm subscriptions are inside the alert window

## Development Notes

- Local development defaults to SQLite
- The FastAPI app creates tables on startup for convenience
- `schema.sql` is intended for MySQL setup
- The repository currently uses server-rendered templates rather than a separate frontend build step
- `.env`, local database files, and other sensitive local artifacts should stay untracked

## License

MIT
