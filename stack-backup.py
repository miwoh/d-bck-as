import datetime
import docker
import docker.errors
import argparse
import logging
import sys
import os

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
        default='astack_default',
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
    # TODO: Remove backups after 3 days (alternatively after an amount of time specified via cl)
    stackapps = ['jira', 'bitbucket', 'confluence', 'crowd']
    for backupfile in os.listdir(args.backup_dir):
        for app in stackapps:
            if app in backupfile:
                if datetime.datetime.fromtimestamp(
                        os.path.getmtime(
                            args.backup_dir + os.sep + backupfile)) < (datetime.datetime.now() - datetime.timedelta(
                                                                                            minutes=args.retention)):
                    os.remove(args.backup_dir + os.sep + backupfile)


def run_backup():
    """ Runs the backup

    Preconditions:
      - command line arguments are parsed
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")

    try:
        client = docker.from_env()
    except docker.errors.APIError as APIERROR:
        log.error('There was an error getting the docker environment. Make sure the daemon is running.')
        log.error(str(APIERROR))
        return 1
    try:
        jirabackup = client.containers.run(
            'centos:latest',
            detach=True,
            volumes={args.backup_dir: {'bind': '/root/connection', 'mode': 'rw'}},
            volumes_from=args.jira_container,
            command='''bash -c "tar -Mcvf /root/connection/jira-home-{timestamp}.backup.tar \
                    /var/atlassian/application-data/jira/ && \
                    tar -Mcvf /root/connection/jira-install-{timestamp}.backup.tar \
                    /opt/atlassian/jira/"'''.format(timestamp=timestamp))

        for line in jirabackup.logs().rsplit('\n'):
            if line != '':
                # TODO: This will not always be an error. Correct that after seeing what the most likely outcomes are.
                log.error(line)

        confluencebackup = client.containers.run(
             'centos:latest',
             detach=True,
             volumes={args.backup_dir: {'bind': '/root/connection', 'mode': 'rw'}},
             volumes_from=args.confluence_container,
             command='''bash -c "tar -Mcvf /root/connection/confluence-home-{timestamp}.backup.tar \
                    /var/atlassian/application-data/confluence/ && \
                    tar -Mcvf /root/connection/confluence-install-{timestamp}.backup.tar \
                    /opt/atlassian/confluence/"'''.format(timestamp=timestamp))

        for line in confluencebackup.logs().rsplit('\n'):
            if line != '':
                log.error(line)

        bitbucketbackup = client.containers.run(
             'centos:latest',
             detach=True,
             volumes={args.backup_dir: {'bind': '/root/connection', 'mode': 'rw'}},
             volumes_from=args.bitbucket_container,
             command='''bash -c "tar -cvf /root/connection/bitbucket-home-{timestamp}.backup.tar \
                    /var/atlassian/application-data/bitbucket/"'''.format(timestamp=timestamp))

        for line in bitbucketbackup.logs().rsplit('\n'):
            if line != '':
                log.error(line)

        crowdbackup = client.containers.run(
             'centos:latest',
             detach=True,
             volumes={args.backup_dir: {'bind': '/root/connection', 'mode': 'rw'}},
             volumes_from=args.crowd_container,
             command='''bash -c "tar -Mcvf /root/connection/crowd-home-{timestamp}.backup.tar \
                    /var/atlassian/application-data/crowd/ && \
                    tar -Mcvf /root/connection/jira-install-{timestamp}.backup.tar \
                    /opt/atlassian/atlassian-crowd-{version}/"'''.format(
                 timestamp=timestamp, version=str(args.crowd_version)))

        for line in crowdbackup.logs().rsplit('\n'):
            if line != '':
                log.error(line)

        jiradb_backup = client.containers.run(
             'postgres:9.4',
             detach=True,
             volumes={args.backup_dir: {'bind': '/root/data', 'mode': 'rw'}},
             environment=["PGPASSWORD=" + args.db_password],
             network=args.network_name,
             command='''bash -c "pg_dump -h db -U jirauser -Fc -w -f \
                    /root/data/jiradb-{timestamp}.pg_dump.fc jiradb"'''.format(timestamp=timestamp))

        for line in jiradb_backup.logs().rsplit('\n'):
            if line != '':
                log.error(line)

        confluencedb_backup = client.containers.run(
             'postgres:9.4',
             detach=True,
             volumes={args.backup_dir: {'bind': '/root/data', 'mode': 'rw'}},
             environment=args.db_password,
             network=args.network_name,
             command='''bash -c "pg_dump -h db -U confluenceuser -Fc -w -f \
                    /root/data/confluencedb-{timestamp}.pg_dump.fc confluencedb"'''.format(timestamp=timestamp))

        for line in confluencedb_backup.logs().rsplit('\n'):
            if line != '':
                log.error(line)

        bitbucketdb_backup = client.containers.run(
             'postgres:9.4',
             detach=True,
             volumes={args.backup_dir: {'bind': '/root/data', 'mode': 'rw'}},
             environment=args.db_password,
             network=args.network_name,
             command='''bash -c "pg_dump -h db -U bitbucketuser -Fc -w -f \
                    /root/data/bitbucketdb-{timestamp}.pg_dump.fc bitbucketdb"'''.format(timestamp=timestamp))

        for line in bitbucketdb_backup.logs().rsplit('\n'):
            if line != '':
                log.error(line)

        crowddb_backup = client.containers.run(
            'postgres:9.4',
            detach=True,
            volumes={args.backup_dir: {'bind': '/root/data', 'mode': 'rw'}},
            environment=args.db_password,
            network=args.network_name,
            command='''bash -c "pg_dump -h db -U crowduser -Fc -w -f \
                   /root/data/crowddb-{timestamp}.pg_dump.fc crowddb"'''.format(timestamp=timestamp))

        for line in crowddb_backup.logs().rsplit('\n'):
            if line != '':
                log.error(line)

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
    #run_backup()


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
                            format='%(asctime)s %(levelname)-5s %(module)-15s %(message)s',
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
