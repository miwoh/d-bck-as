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

To switch between log modes, use the ``--log-level`` switch as described in *Usage*.

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

The general usage of `stack-backup.py` is described by calling `python stack-backup.py --help`.
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

Default values are assumed for the common use cases. These values are:

| Option | Value |
| --- | --- |
| --backup-dir | $PWD/backup |
| --jira-container | astack_jira_1 |
| --confluence-container | astack_confluence_1 |
| --bitbucket-container | astack_bitbucket_1 |
| --crowd-container | astack_crowd_1 |
| --crowd-version | 2.10.1 |
| --network-name | astack_default |
| --retention | 3 |

**Note**

This only applies for usage with command line arguments. If a configuration file
is provided, it is assumed that every value is present in it.

## Backup
An example for running the backup without the configuration file, and with the standard ASERVO Stack containers 
could look like this:

python stack-backup.py \
--backup-dir full/path/to/desired/backupdir \ 
--crowd-version 9.99.9 \
--db-password fancypass \
--retention 10

This would backup all the standard containers, as well as the crowd container contents of
version 9.99.9, while storing everything in /path/to/backupdir with a retention
period of 10 days. The --db-password is obviously for loggin in to the 
databases.

**Note**

The --db-password **or** the --config option must be set in order for the 
script to work (or, more precisely, to backup the databases). 

## Configuration

An example configuration file is provided below. 
```
[global]
backup_dir=/full/path/to/desired/backupdir
jira_container=astack_jira_1
confluence_container=astack_confluence_1
bitbucket_container=astack_bitbucket_1
crowd_container=astack_crowd_1
crowd_version=2.10.1
network_name=bridge
db_password=password
retention=1 
```

**Note**

As of now, the script only checks for the existence of the file/the ``global``
section. Make sure all the values shown above are present in the configuration
file if you use one. 

TODO: Improve script


## Exit Codes

| Code | Meaning |
| --- | --- |
| 99001 | The directory for the log file could not be created |
| 99002 | Insufficient permissions to write the log file |
| 99003 | The backup directory could not be created |
| 99004 | The config file does'nt exist or is missing the ``global`` section |
| 99005 | Neither a config file nor a DB password were provided |
| 99006 | A database backup failed |
| 99007 | Docker API Error |
| 99008 | Configfile Error (one or more used values are missing) |
| 99009 | A database backup failed |

## TODOS
Make sure the backups (AND LOGS) can be stored on mounted filesystems 

