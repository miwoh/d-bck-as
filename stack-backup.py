import datetime
import docker
import docker.errors
import argparse
import logging
import sys
import os


def get_cl_options():
    """ Builds the parser and returns the arguments."""
    parser = argparse.ArgumentParser(
        description="Python SVN Backup Script")
    parser.add_argument(
        "--backup-dir", action="store", dest="backup_dir", metavar="", required=True,
        help="Path to the backup directory.")
    parser.add_argument(
        "--jira-container", action="store", dest="jira_container", metavar="", required=False,
        help="Name of the jira container to be backed up.")
    parser.add_argument(
        "--confluence-container", action="store", dest="confluence_container", metavar="", required=False,
        help="Name of the confluence container to be backed up.")
    parser.add_argument(
        "--bitbucket-container", action="store", dest="bitbucket_container", metavar="", required=False,
        help="Name of the bitbucket container to be backed up.")
    parser.add_argument(
        "--crowd-container", action="store", dest="crowd_container", metavar="", required=False,
        help="Name of the crowd container to be backed up.")
    parser.add_argument(
        "--crowd-version", action="store", dest="crowd_version", metavar="", required=False,
        help="Version of the crowd instance.")
    parser.add_argument(
        "--network-name", action="store", dest="network_name", metavar="", required=False,
        help="Name of the docker network.")
    parser.add_argument(
        "--log-level", action="store", dest="log_level", metavar="", required=False,
        help="Log level. From most to least information: DEBUG, INFO, WARNING, ERROR or CRITICAL")
    arguments = parser.parse_args()
    return arguments


def run_backup():
    """ Runs the backup

    Preconditions:
      - command line arguments are parsed
    """
    timestamp = datetime.datetime.now()

    try:
        client = docker.from_env()
    except docker.errors.APIError as APIERROR:
        log.error("There was an error getting the docker environment. Make sure the daemon is running.")
        log.error(APIERROR)
        return 1

    try:
        jirabackup = client.containers.run("centos:latest",
                                           detach=True,
                                           volumes_from=args.jira_container,
                                           command="""tar -Mcvf /root/connection/jira-home-{timestamp}.backup.tar 
                                                    /var/atlassian/application-data/jira/ && 
                                                    tar -Mcvf /root/connection/jira-install-${timestamp}.backup.tar 
                                                    /opt/atlassian/jira/""".format(timestamp=timestamp))
        for line in jirabackup.logs().rsplit('\n'):
            if line != '':
                log.error(line)

        confluencebackup = client.containers.run("centos:latest",
                                                 detach=True,
                                                 volumes_from=args.confluence_container,
                                                 command="""tar -Mcvf /root/connection/jira-home-{timestamp}.backup.tar 
                                                        /var/atlassian/application-data/jira/ && 
                                                        tar -Mcvf /root/connection/jira-install-${timestamp}.backup.tar 
                                                        /opt/atlassian/jira/""".format(timestamp=timestamp))
    except docker.errors.APIError as APIERROR:
        log.error(APIERROR)
        return 1


def init_log():
    """ Writes DEBUG values to troubleshoot the script if necessary

    Preconditions:
      - command line arguments are parsed
    """
    log.debug("#" * 30 + " D E B U G M O D E " + "#" * 30)
    log.debug("%s has been called with the following parameters:" % sys.argv[0])
    log.debug("Backup Path: %s" % args.backup_dir)
    log.debug("Jira Container Name: %s" % args.jira_container)
    log.debug("Confluence Container Name: %s" % args.confluence_container)
    log.debug("Bitbucket Container Name: %s" % args.bitbucket_container)
    log.debug("Crowd Container Name: %s" % args.crowd_container)
    log.debug("Crowd Instance Version: %s" % args.crowd_version)
    log.debug("Docker Network Name: %s" % args.network_name)


def main():
    run_backup()


if __name__ == "__main__":
    logdir = os.path.join(os.path.dirname(__file__), "log")
    if not os.path.exists(logdir):
        try:
            os.makedirs(logdir)
        except OSError as ex:
            sys.stderr.write("Error creating log directory: " + str(ex))
            sys.exit(1)
    logfile = os.path.join(logdir, "backup.log")
    args = get_cl_options()
    logmodes = [
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL"
        ]
    try:
        logging.basicConfig(filename=logfile,
                            format="%(asctime)s %(levelname)-5s %(module)-15s %(message)s",
                            level=os.environ.get(
                                 "LOGLEVEL",
                                 "INFO" if (args.log_level is None) or (args.log_level.upper() not in logmodes)
                                 else args.log_level.upper()))
    except IOError as ex:
        sys.stderr.write("Insufficient permissions to write log file. Exiting...")
        sys.exit(1)

    log = logging.getLogger("StackBackup")
    # Log initialization with given values (for testing)
    init_log()
    sys.exit(main())
