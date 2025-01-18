import yaml
from telebot import TeleBot

# Load the config file
with open('./src/telegram_bot/conf/config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Dynamically import the modules listed in the config file
apps = config['apps']
imported_apps = {
    app: __import__(f'telegram_bot.api.handlers.apps.{app}', fromlist=[''])
    for app in apps
}

def register_handlers(bot: TeleBot):
    for app in imported_apps.values():
        app.register_handlers(bot)