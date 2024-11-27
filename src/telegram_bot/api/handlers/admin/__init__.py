from telegram_bot.api.handlers.admin import about, db, grant_admin, menu, public_message


def register_handlers(bot):
    db.register_handlers(bot)
    grant_admin.register_handlers(bot)
    menu.register_handlers(bot)
    public_message.register_handlers(bot)
    about.register_handlers(bot)
