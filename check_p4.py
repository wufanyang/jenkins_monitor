import datetime
import os
import p4pythonic
from logger import logger
from distutils.dir_util import copy_tree
from jenkins import Jenkins
from docker import Docker
import json
import util


class P4Checker(object):
    def __init__(self, conf, local_config_file_path):
        self.conf = conf
        self.p4 = p4pythonic.Perforce(port=self.conf['p4']['port'],
                                      client=self.conf['p4']['client'],
                                      user=self.conf['p4']['user'])
        self.p4.authenticate_with_tickets()
        self.local_config_file_path = local_config_file_path

    def update_docker_if_changes_in_p4(self):
        (is_changed, latest_change_list) = \
            self._are_files_changed_in_p4()
        if is_changed:
            self._sync_files_to_current_working_dir()
            Jenkins().wait_for_shutdown()
            Docker().compose_up()
            self._update_change_list_to_local_config_file(latest_change_list)

    def _are_files_changed_in_p4(self):
        latest_change_list = self._get_latest_change_list()
        if ('last_updated_change_list' not in self.conf['p4']) or \
                self._is_changelist1_newer_than_changelist2(
                    latest_change_list,
                    self.conf['p4']['last_updated_change_list']):
            logger.info('CL {} in p4 is detected'.format(latest_change_list))
            return (True, latest_change_list)
        logger.info('No new CL in p4')
        return (False, None)

    def _sync_files_to_current_working_dir(self):
        self.p4.sync(self.conf['p4']['path'], force_sync=True)
        src = os.path.dirname(self.p4.where(self.conf['p4']['path'])['path'])
        dst = os.path.dirname(__file__)
        copy_tree(src, dst)
        # Make files exectuable, so that health check won't have
        # permission deny.
        util.subprocess_popen('chmod -R +x {}'.format(dst))

    def _get_latest_change_list(self):
        changes = self.p4.get_changes(path=self.conf['p4']['path'],
                                      max_entries=1)
        return changes[0]['change']

    def _update_change_list_to_local_config_file(
            self, last_updated_change_list):
        self.conf['p4']['last_updated_change_list'] = last_updated_change_list
        with open(self.local_config_file_path, 'w') as f:
            f.truncate()
            json.dump(self.conf, f)

    def _get_date_by_changelist(self, changelist):
        return self.p4.get_changelist_info(changelist)['Date']

    def _is_changelist1_newer_than_changelist2(
            self, changelist1, changelist2):
        date1 = self._get_date_by_changelist(changelist1)
        date2 = self._get_date_by_changelist(changelist2)
        date_pattern = r'%Y/%m/%d %H:%M:%S'
        return datetime.datetime.strptime(date1, date_pattern) > \
            datetime.datetime.strptime(date2, date_pattern)
