# ASERVO Stack Backup Script
## Getting Started
Place the script on the server where the Atlassian containers are running.

Make sure the user running the script has the appropriate permissions to:
* Create a backup directory in the specified location
* Create a log directory/file in the installation directory of the script

## Prerequisites
* python 2.7
* pip package manager
  * installed ``docker`` package
* a running docker daemon

TODO: Include installation instructions

## Configuration File  

The script provides the *option* to use a configuration file with appropriate values defined.

To provide a configuration file, use the ``--config`` option when calling the script and specify  the configuration file location like so:  

`python stack-backup.py --config /path/to/config/file.ini`  

If the config file given does not exist, or essential values can't be found in it, the script logs it and exits.

The contents of an example configuration file are described below in the section *Configuration*.  

## Log File  
The log file called "backup.log" is located under the subdirectory "log" in the  same directory as the `stack-backup.py` script. It stores INFO, WARNING, ERROR and CRITICAL entries for all events that satisfy these parameters.  

Additionally, detailed logs describing the ``tar`` processes can be found in the backup directory.

To switch between these modes, use the ``--log-level`` switch as described in *Usage*.

Below is an example output which describes the parameters of some such log lines:  

| date | time, ms | loglevel | process | message |  
| --- | --- | --- | --- | --- |  
| 2018-09-07 | 15:36:09,430 | INFO | stack-backup | Information Text |  
| 2018-09-07 | 15:36:10,430 | ERROR | stack-backup | Error Text |  
| 2018-09-07 | 15:36:11,430 | WARNING| stack-backup | Warning Text |  
| 2018-09-07 | 15:36:12,430 | CRITICAL| connectionpool | Critical Text |

## Usage  

Use python to execute the script: `python /your/chosen/path/to/stack-backup.py`  

The `/your/chosen/path/to` will be omitted when describing usage for the rest of this document.  

Use full paths (without trailing slash) only.

The general usage of `svnbackup.py` is described by calling `python stack-backup.py --help`.
```
usage: stack-backup.py [-h] [--backup-dir [BACKUP_DIR]]
                       [--jira-container [JIRA_CONTAINER]]
                       [--confluence-container [CONFLUENCE_CONTAINER]]
                       [--bitbucket-container [BITBUCKET_CONTAINER]]
                       [--crowd-container [CROWD_CONTAINER]]
                       [--crowd-version [CROWD_VERSION]]
                       [--network-name [NETWORK_NAME]]
                       [--db-password [DB_PASSWORD]] [--retention [RETENTION]]
                       [--log-level [LOG_LEVEL]] [--config [CONFIGPATH]] [-v]

ASERVO Stack Backup

optional arguments:
  -h, --help            show this help message and exit
  --backup-dir [BACKUP_DIR]
                        Path to the backup directory.
  --jira-container [JIRA_CONTAINER]
                        Name of the jira container to be backed up.
  --confluence-container [CONFLUENCE_CONTAINER]
                        Name of the confluence container to be backed up.
  --bitbucket-container [BITBUCKET_CONTAINER]
                        Name of the bitbucket container to be backed up.
  --crowd-container [CROWD_CONTAINER]
                        Name of the crowd container to be backed up.
  --crowd-version [CROWD_VERSION]
                        Version of the crowd instance.
  --network-name [NETWORK_NAME]
                        Name of the docker network.
  --db-password [DB_PASSWORD]
                        Password to login to the databases.
  --retention [RETENTION]
                        Retention period of existing backups in days. Default is 3.
  --log-level [LOG_LEVEL]
                        From most to least information: DEBUG, INFO, WARNING, ERROR or CRITICAL.
  --config [CONFIGPATH]
                        Path to the configuration file.
  -v, --version         
                        show program's version number and exit
```
