"""Handler to show information about the application configuration."""
import logging
import os

from omegaconf import OmegaConf

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configurations
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
config_path = os.path.join(project_dir, "conf" , "config.yaml")
config = OmegaConf.load(config_path)

def register_handlers(bot):
    """Register about handlers"""
    logger.info("Registering `about` handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "about")
    def about_handler(call):
        user_id = call.from_user.id

        config_str = OmegaConf.to_yaml(config)

        # Send config
        bot.send_message(user_id, f"```yaml\n{config_str}\n```", parse_mode="Markdown")
