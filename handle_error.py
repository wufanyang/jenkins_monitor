from logger import logger
from ori_mail import mail
import templates


class ErrorHanlder(object):
    def __init__(self,
                 mail_from_address=r'fanyang.wu@ni.com',
                 mail_to_address=r'fanyang.wu@ni.com'):
        self.mail_from_address = mail_from_address
        self.mail_to_address = mail_to_address

    def handle_error(self, msg_to_log, mail_content, mail_subject):
        content = {'msg': mail_content}
        try:
            self.send_mail(content, mail_subject)
        except Exception as e:
            logger.error(repr(e))
        logger.error(msg_to_log)

    def send_mail(self, content, subject):
        m = mail.Mail()

        m.populate_test_notification_content(
            content, template=templates.DefaultHTML())

        m.send(from_address=self.mail_from_address,
               to_address=self.mail_to_address,
               subject=subject)
