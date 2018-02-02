from mako.template import Template
import os


class DefaultHTML:
    """This is the default html mail template class.
       The data object it accepts is a dictionary that has the following keys:
       {
           'msg':  str
       }
    """
    def populate(self, data):
        template_path = os.path.join(os.path.dirname(__file__),
                                     'html_notification.tmpl')
        self.content = Template(filename=template_path) \
            .render(**data) \
            .replace("\r\n", "\n")

    def get_content(self):
        return self.content

    def get_content_type(self):
        return 'html'
