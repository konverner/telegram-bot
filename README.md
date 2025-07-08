## Telegram Bot Template

This is a simple template for creating a Telegram bot using Python. It uses the `pyTelegramBotAPI` library for interaction with Telegram's API and SQLAlchemy for database interactions. The bot logs messages, saves user details, and can be deployed using Docker.

## Structure

The project is structured as follows:



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
2. Enter values in `.env.example` and rename it to `.env`.
3. Install the dependencies with `pip install .`.
4. Run the bot with `python -m src.telegram_bot.main`.

## Docker

To run this application in a Docker container, follow these steps:

1. Build the Docker image with `docker build -t telegram-bot .`.
2. Run the Docker container with `docker run -p 80:80 telegram-bot`.
