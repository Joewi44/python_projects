import logging
import logging.config
import os
from logging.handlers import TimedRotatingFileHandler

def setup_logging(default_level=logging.INFO):
    os.makedirs('logs', exist_ok=True)

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': default_level,
            },
            'file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'standard',
                'level': default_level,
                'filename': 'logs/app.log',
                'when': 'midnight',      # Rotate at midnight
                'interval': 1,           # Every 1 day
                'backupCount': 10,       # Keep 10 backup files
                'encoding': 'utf-8',
                'utc': False,            # Use local time for rotation
                'delay': False,
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': default_level,
        },
    }

    logging.config.dictConfig(logging_config)

