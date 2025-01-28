import logging
import logging.config
import os
from datetime import datetime

from omegaconf import OmegaConf

from ....db.database import export_all_tables

# Load configurations
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
config_path = os.path.join(project_dir, "conf", "config.yaml")
config = OmegaConf.load(config_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register_handlers(bot):
    logger.info("Registering admin database handler")

    @bot.callback_query_handler(func=lambda call: call.data == "export_data")
    def export_data_handler(call, data):
        user = data["user"]

        # Export data
        export_dir = f'./data/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.makedirs(export_dir)
        try:
            export_all_tables(export_dir)
            for table in config.db.tables:
                # save as excel in temp folder and send to a user
                filename = f"{export_dir}/{table}.csv"
                bot.send_document(user.id, open(filename, "rb"))
                # remove the file
                os.remove(filename)
        except Exception as e:
            bot.send_message(user.id, str(e))
            logger.error(f"Error exporting data: {e}")
