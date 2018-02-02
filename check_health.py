from docker import Docker
from logger import logger


class HealthChecker(object):
    def __init__(self, conf, error_hanlder):
        self.conf = conf
        self.error_hanlder = error_hanlder

    def report_and_recover_docker_if_unhealthy(self):
        if 'max_continuous_retry_times' in self.conf:
            max_retry = self.conf['max_continuous_retry_times']
        else:
            max_retry = 3  # default value
        current_retry = 0
        docker = Docker()
        while True:
            if not docker.is_container_healthy:
                if (max_retry <= current_retry):
                    logger.error('docker unhealthy, exceed {} times'.format(
                        max_retry))
                    break

                mail_subject = 'fail health check'
                mail_content = docker.get_container_health_log()
                self.error_hanlder.handle_error(
                    mail_subject, mail_content, mail_subject)

                docker.compose_up()
                current_retry += 1
            else:
                break
