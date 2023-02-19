#!/bin/bash

# This example script starts the Test Minecraft Server and the Backup Agent in 
# seperate detached screen sessions. 

screen -S Minecraft -d -m /bin/bash -c "cd ./TestServer ; ./run.sh ; read"
screen -S Backup    -d -m /bin/bash -c "python mcbackup.py ; read"
