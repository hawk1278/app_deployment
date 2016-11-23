#!/usr/bin/env python
import logging
from logging.handlers import RotatingFileHandler
import os

def log_it(**kwargs):
    logger = logging.getLogger(kwargs['name'])
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    rlh = logging.handlers.RotatingFileHandler(os.path.join(kwargs['logpath'], kwargs['logname']), maxBytes=102400, backupCount=100)
    rlh.setLevel(logging.DEBUG)
    rlh.setFormatter(formatter)
    logger.addHandler(rlh)
    return logger
