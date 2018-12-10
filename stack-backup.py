import datetime
import docker
import docker.errors
import argparse
import logging
import sys
import os
from time import sleep

from _version import __version__


def get_cl_options():
    """ Builds the parser and returns the arguments."""
    parser = argparse.ArgumentParser(description='Script')
    parser.add_argument(
        '--backup-dir', action='store', dest='backup_dir', nargs='?',
        default='$PWD/backup',
        help='Path to the backup directory.')
    parser.add_argument(
        '--jira-container', action='store', dest='jira_container', nargs='?',
        default='astack_jira_1',
        help='Name of the jira container to be backed up.')
    parser.add_argument(
        '--confluence-container', action='store', dest='confluence_container', nargs='?',
        default='astack_confluence_1',
        help='Name of the confluence container to be backed up.')
    parser.add_argument(
        '--bitbucket-container', action='store', dest='bitbucket_container', nargs='?',
        default='astack_bitbucket_1',
        help='Name of the bitbucket container to be backed up.')
    parser.add_argument(
        '--crowd-container', action='store', dest='crowd_container', nargs='?',
        default='astack_crowd_1',
        help='Name of the crowd container to be backed up.')
    parser.add_argument(
        '--crowd-version', action='store', dest='crowd_version', nargs='?',
        default='2.10.1',
        help='Version of the crowd instance.')
    parser.add_argument(
        '--network-name', action='store', dest='network_name', nargs='?',
        default='bridge',
        help='Name of the docker network.')
    parser.add_argument(
        '--db-password', action='store', dest='db_password', required=True, nargs='?',
        help='Password to login to the databases.')
    parser.add_argument(
        '--retention', action='store', type=int, dest='retention', nargs='?',
        default=3,
        help='Retention period of existing backups in days. Default is 3.')
    parser.add_argument(
        '--log-level', action='store', dest='log_level', nargs='?',
        default='INFO',
        help='From most to least information: DEBUG, INFO, WARNING, ERROR or CRITICAL.')
    parser.add_argument(
        '-v', '--version', action='version', version='{version}'.format(version=__version__))
    arguments = parser.parse_args()
    return arguments


def remove_expired_backups():
    """ Removes backups older than the specified retention period (or 3 days if omitted)

    Preconditions:
      - command line arguments are parsed
    """

    # Im not removing any logs here, and that's by design. Consider log rotation.
    stackapps = ['jira', 'bitbucket', 'confluence', 'crowd']
    oldbackupfound = False
    log.info('#' * 10 + ' Atlassian Stack Backup Starting! ' + '#' * 10)
    log.info('Removing files older than %d day/s...' % args.retention)
    for backupfile in os.listdir(args.backup_dir):
        for app in stackapps:
            if app in backupfile:
                if datetime.datetime.fromtimestamp(
                        os.path.getmtime(
                            args.backup_dir + os.sep + backupfile)) < (datetime.datetime.now() - datetime.timedelta(
                                                                                            minutes=args.retention)):
                    os.remove(args.backup_dir + os.sep + backupfile)
                    log.debug('%s' % args.backup_dir + os.sep + backupfile)
                    oldbackupfound = True
    if not oldbackupfound:
        log.info('None found.')
    log.info('Done removing old files!')



def run_backup():
    """ Runs the backup

    Preconditions:
      - command line arguments are parsed
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    # helper variable for checking for found errors in the backup output (because one line suffices in backup.log)
    found_error = False
    try:
        client = docker.from_env()
    except docker.errors.APIError as APIERROR:
        log.critical('Unable to get the docker environment. Make sure the daemon is running.')
        log.critical(str(APIERROR))
        return 1
    try:
        client.containers.run(
            'centos:latest',
            detach=True,
            remove=True,
            volumes={args.backup_dir: {'bind': '/root/connection', 'mode': 'rw'}},
            volumes_from=args.jira_container,
            command='''bash -c "tar -cvf /root/connection/jira-home-{timestamp}.backup.tar \
                    /var/atlassian/application-data/jira/ &> \
                    /root/connection/jira-bck-{timestamp}.tar.log && \
                    tar -cvf /root/connection/jira-install-{timestamp}.backup.tar \
                    /opt/atlassian/jira/ &>> \
                    /root/connection/jira-bck-{timestamp}.tar.log"'''.format(timestamp=timestamp))
        # This is necessary to let the process finish before checking its output
        sleep(1)
        jiralog = open(args.backup_dir + os.sep + 'jira-bck-{timestamp}.tar.log'.format(
            timestamp=timestamp), 'r')
        for line in jiralog.readlines():
            if "Cannot" in line or "Exiting" in line:
                found_error = True
        jiralog.close()
        if found_error:
            log.error("Unable to finish JIRA backup!")
            log.error("Details in %s" % args.backup_dir + '/jira-bck-{timestamp}.tar.log'.format(
                timestamp=timestamp))
            found_error = False
        else:
            log.info("JIRA Backup Finished without errors. Rejoice!")

        client.containers.run(
             'centos:latest',
             detach=True,
             remove=True,
             volumes={args.backup_dir: {'bind': '/root/connection', 'mode': 'rw'}},
             volumes_from=args.confluence_container,
             command='''bash -c "tar -cvf /root/connection/confluence-home-{timestamp}.backup.tar \
                    /var/atlassian/application-data/confluence/ &> \
                    /root/connection/confluence-bck-{timestamp}.tar.log && \
                    tar -cvf /root/connection/confluence-install-{timestamp}.backup.tar \
                    /opt/atlassian/confluence/ &>> \
                    /root/connection/confluence-bck-{timestamp}.tar.log"'''.format(timestamp=timestamp))
        sleep(1)
        confluencelog = open(args.backup_dir + os.sep + 'confluence-bck-{timestamp}.tar.log'.format(
            timestamp=timestamp), 'r')
        for line in confluencelog.readlines():
            if "Cannot" in line or "Exiting" in line:
                found_error = True
        confluencelog.close()
        if found_error:
            log.error("Unable to finish Confluence backup!")
            log.error("Details in %s" % args.backup_dir + '/confluence-bck-{timestamp}.tar.log'.format(
                timestamp=timestamp))
            found_error = False
        else:
            log.info("Confluence Backup Finished without errors. Rejoice!")

        client.containers.run(
             'centos:latest',
             detach=True,
             remove=True,
             volumes={args.backup_dir: {'bind': '/root/connection', 'mode': 'rw'}},
             volumes_from=args.bitbucket_container,
             command='''bash -c "tar -cvf /root/connection/bitbucket-home-{timestamp}.backup.tar \
                    /var/atlassian/application-data/bitbucket/ &> \
                    /root/connection/bitbucket-bck-{timestamp}.tar.log"'''.format(timestamp=timestamp))
        sleep(1)
        bitbucketlog = open(args.backup_dir + os.sep + 'bitbucket-bck-{timestamp}.tar.log'.format(
            timestamp=timestamp), 'r')
        for line in bitbucketlog.readlines():
            if "Cannot" in line or "Exiting" in line:
                found_error = True
        bitbucketlog.close()
        if found_error:
            log.error("Unable to finish Bitbucket backup!")
            log.error("Details in %s" % args.backup_dir + '/bitbucket-bck-{timestamp}.tar.log'.format(
                timestamp=timestamp))
            found_error = False
        else:
            log.info("Bitbucket Backup Finished without errors. Rejoice!")

        client.containers.run(
             'centos:latest',
             detach=True,
             remove=True,
             volumes={args.backup_dir: {'bind': '/root/connection', 'mode': 'rw'}},
             volumes_from=args.crowd_container,
             command='''bash -c "tar -cvf /root/connection/crowd-home-{timestamp}.backup.tar \
                    /var/atlassian/application-data/crowd/  &> \
                    /root/connection/crowd-bck-{timestamp}.tar.log && \
                    tar -cvf /root/connection/crowd-install-{timestamp}.backup.tar \
                    /opt/atlassian/atlassian-crowd-{version}/ &>> \
                    /root/connection/crowd-bck-{timestamp}.tar.log"'''.format(
                                                                timestamp=timestamp, version=str(args.crowd_version)))
        sleep(1)
        crowdlog = open(args.backup_dir + os.sep + 'crowd-bck-{timestamp}.tar.log'.format(
            timestamp=timestamp), 'r')
        for line in crowdlog.readlines():
            if "Cannot" in line or "Exiting" in line:
                found_error = True
        crowdlog.close()
        if found_error:
            log.error("Unable to finish Crowd backup!")
            log.error("Details in %s" % args.backup_dir + '/crowd-bck-{timestamp}.tar.log'.format(
                timestamp=timestamp))
            found_error = False
        else:
            log.info("Crowd Backup Finished without errors. Rejoice!")

        jiradb_backup = client.containers.run(
             'postgres:9.4',
             detach=True,
             remove=True,
             volumes={args.backup_dir: {'bind': '/root/data', 'mode': 'rw'}},
             environment=["PGPASSWORD=" + args.db_password],
             network=args.network_name,
             command='''bash -c "pg_dump -h db -U jirauser -Fc -w -f \
                    /root/data/jiradb-{timestamp}.pg_dump.fc jiradb"'''.format(timestamp=timestamp))
        sleep(1)
        for line in jiradb_backup.logs().rsplit('\n'):
            if line != '':
                log.info(line)

        confluencedb_backup = client.containers.run(
             'postgres:9.4',
             detach=True,
             remove=True,
             volumes={args.backup_dir: {'bind': '/root/data', 'mode': 'rw'}},
             environment=["PGPASSWORD=" + args.db_password],
             network=args.network_name,
             command='''bash -c "pg_dump -h db -U confluenceuser -Fc -w -f \
                    /root/data/confluencedb-{timestamp}.pg_dump.fc confluencedb"'''.format(timestamp=timestamp))
        sleep(1)
        for line in confluencedb_backup.logs().rsplit('\n'):
            if line != '':
                log.info(line)

        bitbucketdb_backup = client.containers.run(
             'postgres:9.4',
             detach=True,
             remove=True,
             volumes={args.backup_dir: {'bind': '/root/data', 'mode': 'rw'}},
             environment=["PGPASSWORD=" + args.db_password],
             network=args.network_name,
             command='''bash -c "pg_dump -h db -U bitbucketuser -Fc -w -f \
                    /root/data/bitbucketdb-{timestamp}.pg_dump.fc bitbucketdb"'''.format(timestamp=timestamp))
        sleep(1)
        for line in bitbucketdb_backup.logs().rsplit('\n'):
            if line != '':
                log.info(line)

        crowddb_backup = client.containers.run(
            'postgres:9.4',
            detach=True,
            remove=True,
            volumes={args.backup_dir: {'bind': '/root/data', 'mode': 'rw'}},
            environment=["PGPASSWORD=" + args.db_password],
            network=args.network_name,
            command='''bash -c "pg_dump -h db -U crowduser -Fc -w -f \
                   /root/data/crowddb-{timestamp}.pg_dump.fc crowddb"'''.format(timestamp=timestamp))
        sleep(1)
        for line in crowddb_backup.logs().rsplit('\n'):
            if line != '':
                log.info(line)

    except docker.errors.APIError as APIERROR:
        log.error(str(APIERROR))
        return 1

# TODO: Provide the option (!) to do the backup with a configfile instead of cl arguments


def init_log():
    """ Writes DEBUG values to troubleshoot the script if necessary

    Preconditions:
      - command line arguments are parsed
    """
    log.debug('#' * 30 + ' D E B U G M O D E ' + '#' * 30)
    log.debug('%s has been called with the following parameters:' % sys.argv[0])
    log.debug('Backup Path: %s' % args.backup_dir)
    log.debug('Jira Container Name: %s' % args.jira_container)
    log.debug('Confluence Container Name: %s' % args.confluence_container)
    log.debug('Bitbucket Container Name: %s' % args.bitbucket_container)
    log.debug('Crowd Container Name: %s' % args.crowd_container)
    log.debug('Crowd Instance Version: %s' % args.crowd_version)
    log.debug('Docker Network Name: %s' % args.network_name)


def main():
    remove_expired_backups()
    run_backup()


if __name__ == '__main__':
    logdir = os.path.join(os.path.dirname(__file__), 'log')
    if not os.path.exists(logdir):
        try:
            os.makedirs(logdir)
        except OSError as ex:
            sys.stderr.write('Error creating log directory: ' + str(ex))
            sys.exit(1)

    logfile = os.path.join(logdir, 'backup.log')
    args = get_cl_options()

    logmodes = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    try:
        logging.basicConfig(filename=logfile,
                            format='%(asctime)s %(levelname)-5s %(module)-14s %(message)s',
                            level=os.environ.get(
                                 'LOGLEVEL',
                                 'INFO' if (args.log_level is None) or (args.log_level.upper() not in logmodes)
                                 else args.log_level.upper()))
    except IOError as ex:
        sys.stderr.write('Insufficient permissions to write log file. Exiting...')
        sys.exit(1)

    log = logging.getLogger('StackBackup')

    # Log initialization with given values (for testing)
    init_log()

    if not os.path.exists(args.backup_dir):
        log.debug("Backup directory doesn't exist. Creating %s" % args.backup_dir)
        try:
            os.makedirs(args.backup_dir)
        except OSError as ex:
            log.critical('Error creating backup directory: ' + str(ex))
            sys.exit(1)

    sys.exit(main())
