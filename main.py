#!/usr/bin/python

from argparse import ArgumentParser
from check_p4 import P4Checker
from check_health import HealthChecker
import fcntl
from handle_error import ErrorHanlder
import json
import os
import sys
import traceback


def parse_args(args):
    parser = ArgumentParser(
        description="Monitor and update Jenkins master.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check_p4', action='store_true',
                       help='check changes in p4')
    group.add_argument('--check_health', action='store_true',
                       help='check docker container health')
    return parser.parse_args(args)


def get_job_owned_lock(job_type):
    def wrapper_func(func):
        def wrapper(*args, **kwds):
            if job_type == '--check_p4':
                lock_file_path = '/var/lock/check_p4.lock'
            else:
                lock_file_path = '/var/lock/check_health.lock'
            fp = open(lock_file_path, 'w')
            try:
                # exclusive, non-block
                fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return func(*args, **kwds)
            # other instance of the same cron job is running, just exit.
            except IOError:
                exit(0)
            finally:
                fp.close()
        return wrapper
    return wrapper_func


def get_jobs_shared_lock(func):
    def wrapper(*args, **kwds):
        lock_file_path = '/var/lock/check_P4_health.lock'
        fp = open(lock_file_path, 'w')
        try:
            fcntl.lockf(fp, fcntl.LOCK_EX)  # block
            return func(*args, **kwds)
        finally:
            fp.close()
    return wrapper


def get_error_hanlder(conf):
    try:
        return ErrorHanlder(conf['email']['from_address'],
                            conf['email']['to_address'])
    except KeyError:
        return ErrorHanlder()


def read_conf(local_config_file_path):
    try:
        with open(local_config_file_path, 'r') as f:
            conf = json.load(f)
        return conf
    except (IOError, ValueError) as e:
        ErrorHanlder().handle_error(
            msg_to_log=traceback.format_exc(),
            mail_content=repr(e),
            mail_subject=repr(e))
        exit(1)


@get_job_owned_lock(sys.argv[1])
@get_jobs_shared_lock
def main(args):
    local_config_file_path = os.path.join(
        os.path.dirname(__file__), 'config.json')
    conf = read_conf(local_config_file_path)
    error_hanlder = get_error_hanlder(conf)

    try:
        if args.check_p4:
            p4_checker = P4Checker(conf, local_config_file_path)
            p4_checker.update_docker_if_changes_in_p4()
        else:
            health_checker = HealthChecker(
                conf['health_check'], error_hanlder)
            health_checker.report_and_recover_docker_if_unhealthy()
    except Exception as e:
        mail_content = ("exception: {}\n traceback: {}".format(
            repr(e), traceback.format_exc()))
        error_hanlder.handle_error(
            msg_to_log=traceback.format_exc(),
            mail_content=mail_content,
            mail_subject=type(e).__name__)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    main(args)
