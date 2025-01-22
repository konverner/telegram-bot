## Telegram Bot Template

This is a simple template for creating a Telegram bot using Python. It uses the `pyTelegramBotAPI` library for interaction with Telegram's API and SQLAlchemy for database interactions. The bot logs messages, saves user details, and can be deployed using Docker.

## Structure

The project is structured as follows:

`main.py` - The main file that defines and runs the bot.

`core/` - The module that contains services for the bot's applications.

`conf/config.yaml` - The base configuration for the bot: name, version, timezone, applications enabled, database settings, etc.

`conf/apps/` - Config files for user's applications

`conf/admin/` - Config files for admin's applications

`api/handlers/apps` - The user's application handles for interactions with the Telegram API.

`api/handlers/admin` - The admin's application handles for interactions with the Telegram API.

`db/database.py` - The file that handles interactions with the database.

`db/models.py` - Models for database tables.

`db/crud.py` - CRUD operations for database.

`tests/` - The directory that contains the tests for the application.

`Dockerfile` - The file that defines the Docker container for this application.

## In-built admin applications

### Send public message to all users of the bot

### Grant admin rights to other user

### Export database tables of the bot

### About

## In-built user applications

### LLM

Sending queries to LLM.

### Google Drive

Upload and download file on Google Drive.

### Google Sheets

Wrtie records to Google Sheets.

### Resource

Creating and downloading a csv file.

### Language

Change the language.

## Setup

1. Clone this repository.
2. Create a `.env` file in the root directory and add your database connection string and bot token.
3. Install the dependencies with `pip install .`.
4. Run the bot with `python src/telegrab_bot/main.py`.

## Docker

To run this application in a Docker container, follow these steps:

1. Build the Docker image with `docker build -t telegram-bot .`.
2. Run the Docker container with `docker run -p 80:80 telegram-bot`.
