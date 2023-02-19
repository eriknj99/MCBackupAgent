# MCBackupAgent
A robust Minecraft server backup solution

## Features
- Custom backup interval
- Custom backup directory
- Backup skipping during inactivity to save space
- Save management during backups to prevent curruption
- Communicates with server using RCOM
- Resistant to server crashes and restarts. 
- Fancy in game log and information display

![in_game](https://user-images.githubusercontent.com/11905989/219933087-8bb72ddf-b235-41d0-9579-e023a3ff903b.png)

## Setup 
- Set enable-rcon to true in server.properties
- Set rcon.password in server.properties
  - Note: The Minecraft Server must be restarted for the changes to take effect
- Create the backup directory and note its absolute path
- Edit config.json as described below
- Start MCBackupAgent with : `python mcbackup.py`

## Configuration
Configuration is managed through config.json. All options are needed. 
| Option          | Description           | Hint                                       |
|-----------------|-----------------------|--------------------------------------------|
| host            | RCOM server IP        | Usually 127.0.0.1                          |
| port            | RCOM server port      | Same as rcon.port in server.properties     |
| password        | RCOM server password  | Same as rcon.password in server.properties |
| world_path      | Path to the world dir | Absolute path recomended                   |
| backup_path     | Path to backup dir    | Absolute path recomended                   |
| backup_interval | Time between backups  | Seconds                                    |

## Example
This repository contains a working example configuration of MCBackupAgent. The `run.sh` script in the repository root will start MCBackupAgent and a Minecraft server (1.19.3). The provided configuration should work out of the box.

## Caveats
- MCBackupAgent is designed for Linux. MacOS might work. Windows will not.
- MCBackupAgent should be run on the same computer as the Minecraft server. 
- Old backups are never automatically cleaned up. 




