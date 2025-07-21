## Telegram Bot Template

This is a template for creating a Telegram bot using Python. It uses the `pyTelegramBotAPI` library for interaction with the Telegram Bot API and SQLAlchemy for database interactions. The bot logs messages, saves user details, and can be deployed using Docker.


## Structure

The project is composed of features. Each feature is defined with:

- Data models: They represent entities in the database.

- Service: It performs business logic with the database.

- Config: It is a YAML file that keeps changeable values like strings and parameters of the feature.

- Handlers: They listen to Telegram actions, similar to routes in classic API architecture.

- Markup: It defines functions for generating UI elements.

### Core Features

Core features are based completely on Telegram, i.e., without external calls. Core features implement a user-item pattern. Users can:

- View options via the main menu using the `/menu` command: [src/app/menu](src/app/menu)

- Create, edit, and delete items (notes) via the main menu. Items are stored in the database table `items`: [src/app/items](src/app/items)

- Change language: [src/app/language](src/app/language)

User information is stored in the `users` database table.

### Admin Features

Admin features allow performing operations on users. The admin menu is available for users with the `admin` role and can be invoked with the `/admin` command. It includes the following functions:

- Send public messages to all users of the bot: [src/app/public_message](src/app/public_message)

- Grant admin rights to other users, block users from using the bot: [src/app/users](src/app/users)

- Export database tables of the bot: [src/app/admin](src/app/admin)

### Plugin Features

Plugins are features based on external services and can be plugged in and out easily without breaking the bot.

- OpenAI: It allows consuming OpenAI services like GPT and DALL-E

- Google Drive: It allows uploading and downloading files on Google Drive.

- Google Sheets: It allows creating sheets and writing records on Google Sheets.

- yt-dlp: It allows downloading videos from YouTube and other services supported by yt-dlp.

## Launch

You can run the project directly on your machine or in Docker.

### Setup

1. Clone this repository.
2. Enter values in `.env.example` and rename it to `.env`.

### Run Directly

1. Install the dependencies with `pip install .`.
2. Run the bot with `python -m src.app.main`.

### Run in Docker

To run this application in a Docker container, follow these steps:

1. Build the Docker image with `docker build -t telegram-bot .`.
2. Run the Docker container with `docker run telegram-bot`.
1. Build the Docker image with `docker build -t telegram-bot .`.
2. Run the Docker container with `docker run telegram-bot`.
