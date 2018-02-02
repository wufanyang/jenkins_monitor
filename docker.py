from logger import logger
import os
import re
import traceback
import time
import util
import yaml


class ContainerNotFound(Exception):
    pass


class Docker(object):
    def __init__(self):
        self._container_name = None

    @property
    def container_name(self):
        if self._container_name is None:
            docker_conf_file_path = os.path.join(
                os.path.dirname(__file__), 'docker-compose.yml')
            try:
                with open(docker_conf_file_path, 'r') as f:
                    conf = yaml.load(f)
                self._container_name = \
                    conf['services']['jenkins']['container_name']
            except (IOError, yaml.YAMLError, KeyError):
                logger.error(traceback.format_exc())
                self._container_name = 'jenkins_server'
        return self._container_name

    def compose_up(self, retry_times=2):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        compose_up_cmd = 'docker-compose up --build -d'
        for i in range(0, retry_times):
            try:
                util.subprocess_popen(compose_up_cmd)
                break  # succeed
            except util.CalledProcessError as e:
                if i == (retry_times - 1):
                    raise e
                else:
                    logger.error('docker-compose up fail, {}, retrying'.format(
                        repr(e)))
                    continue  # retry

    def get_container_status(self):
        get_status_cmd = r'docker ps -a --filter' \
            + ' name=%s --format "{{.Status}}"' % (self.container_name)
        status = util.subprocess_popen(get_status_cmd).strip()
        if status == '':
            raise ContainerNotFound
        else:
            return status

    @property
    def is_container_healthy(self):
        while True:
            try:
                container_status = self.get_container_status()
                logger.info(container_status)
                # search "(healthy)"
                if re.search('\(healthy\)', container_status):
                    return True
                # search "(health: starting)"
                elif re.search('\(health: *starting\)', container_status):
                    # Wait for container become healthy or unhealthy.
                    time.sleep(120)
                    continue
                else:
                    return False
            except ContainerNotFound:
                logger.info('container {} not found'.format(
                    self.container_name))
                return False

    def get_container_health_log(self):
        cmd = 'docker inspect --format="{{json .State.Health.Log}}" %s' \
            % (self.container_name)
        return util.subprocess_popen(cmd).strip()
