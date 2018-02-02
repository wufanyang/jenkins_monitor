from logger import logger
import requests
from requests.auth import HTTPBasicAuth
import time


class Jenkins(object):
    def __init__(self, scheme='http', host='localhost',
                 port=8080, username='instbuild',
                 password='Welcome123'):
        self.url = r'{}://{}:{}'.format(scheme, host, port)
        self.username = username
        self.password = password

    def _safe_shutdown(self):
        cmd = self.url + '/safeExit'
        logger.info('Trying to {} with username {}, password {}'.format(
            cmd, self.username, self.password))
        requests.post(cmd, auth=HTTPBasicAuth(self.username, self.password))

    def _is_alive(self):
        try:
            r = requests.get(self.url + '/login')
            if r.status_code == 200:
                return True
            else:
                return False
        except requests.exceptions.RequestException:
            return False

    def wait_for_shutdown(self):
        if not self._is_alive():
            logger.info('jenkins not alive before shutdown')
            return
        self._safe_shutdown()
        while True:
            if self._is_alive():
                time.sleep(10)
            else:
                logger.info('shutdown jenkins successfully')
                return
