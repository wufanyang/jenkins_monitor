import logging
import logging.handlers
import platform
import os


if platform.system() == 'Windows':
    log_path = os.path.join(
        os.path.dirname(__file__), "jenkins_monitor.log")
else:
    log_path = '/var/log/jenkins_monitor.log'

logger = logging.getLogger(__name__)
handler = logging.handlers.RotatingFileHandler(
    filename=log_path, mode='a', maxBytes=(2 * 1024 * 1024),
    backupCount=5, delay=True)
formatter = logging.Formatter(
    '%(pathname)s %(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
