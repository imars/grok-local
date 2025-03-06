# grok_local/utils.py
import datetime
from grok_local.config import logger

def what_time_is_it():
    now = datetime.datetime.now(datetime.timezone.utc)
    time_str = now.strftime("%I:%M %p GMT, %B %d, %Y")
    logger.info(f"Time requested: {time_str}")
    return time_str

def report(response):
    return response  # Simple passthrough for now; could add formatting later
