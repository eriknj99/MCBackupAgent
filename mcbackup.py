import mcrcon
import socket
import json
import shutil 
import os.path
import time
from datetime import datetime, timedelta
from threading import Thread

from mc_color_codes import *

# Text colors
# C1 : Primary
# C2 : Accent
C1 = AQUA
C2 = LIGHT_PURPLE

# Util functions

# Take a size in bytes and conver it to a readable format
def format_data(byte):
    if(byte > 1000000000000):
        return f"{round(byte / 1000000000000)} TB"
    if(byte > 1000000000):
        return f"{round(byte / 1000000000)} GB"
    if(byte > 1000000):
        return f"{round(byte / 1000000)} MB"
    if(byte > 1000):
        return f"{round(byte / 1000)} KB"
    return f"{byte} B"

# Take a duration in seconds and convert it to a readable format
def format_time(duration):
    if(duration < 60):
        return str(int(duration)) + "s"

    if(duration < 3600):
        return time.strftime('%M:%S', time.gmtime(int(duration)))

    return time.strftime('%H:%M:%S', time.gmtime(int(duration)))

# Get the size in bytes of a given dir. (Recursive)
def get_dir_size(path:str)->int:
    size = 0
    for path, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    return size

# Get the number of files in a directory
def get_num_files(path:str)->int:
    count = 0
    for root_dir, cur_dir, files in os.walk(path):
        count += len(files)
    return count

class MCBackupAgent:
    
    # Read the config.json file and populate instance variables
    def read_conf(self)->bool:
        try:
            f = open("config.json")
            j = json.load(f)
            self.host            = j["host"]
            self.port            = j["port"]
            self.password        = j["password"]
            self.world_path      = j["world_path"]
            self.backup_path     = j["backup_path"]
            self.backup_interval = j["backup_interval"]
        except:
            print("\nError: Unable to parse config.json")
            return False

        # Check to make sure both paths exist
        if(not os.path.exists(self.world_path)):
            print(f"\nError: The specified world path ({self.world_path}) does not exist")
            return False

        if(not os.path.exists(self.backup_path)):
            print(f"\nError: The specified backup path ({self.backup_path}) does not exist")
            return False

        msg  = f"  host     : {self.host}\n"
        msg += f"  port     : {self.port}\n"
        msg += f"  pass     : {self.password}\n"
        msg += f"  world    : {self.world_path}\n"
        msg += f"  backup   : {self.backup_path}\n"
        msg += f"  interval : {format_time(self.backup_interval)}\n"
        print(msg)

        return True
    
    # Create a socket and login to the rcon server
    # Return an indication of success
    # Note: read_conf must be called before this function
    def connect(self)->bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            return mcrcon.login(self.sock, self.password)
        except:
            return False

    # Execute the given minecraft command and return the result
    def execute(self, cmd:str)->str:
        rsp = mcrcon.command(self.sock, cmd)
        return rsp

    # Check the connection by executing the seed command
    # Possible seed leak here?
    def is_connected(self)->bool:
        try:
            seed = self.execute("seed")
            return len(seed) != 0
        except:
            return False

    # Get the number of players currently on the server
    def get_player_count(self)->int:
        try:
            rsp = self.execute("list")
            return int(rsp.split(" ")[2])
        except:
            return 0
    
    # Say the given message in global chat
    # Using tellraw does not allow \n for some reason
    # so lines are sent over multiple commands
    def say(self, txt:str):
        for line in txt.split("\n"):
            self.execute(f"tellraw @a \"{line}\"")

    # Say some info about the backups in gamechat
    def say_info(self):
        world_size = get_dir_size(self.world_path)
        backup_size = get_dir_size(self.backup_path)
        num_backups = get_num_files(self.backup_path)
        dt_next_backup = datetime.now() + timedelta(seconds=self.backup_interval)

        # Minecraft font isn't monospace. This spacing is as close as I can get
        msg  = f"Current World size       {C2}{BOLD}{format_data(world_size)}{RESET_ALL}\n"
        msg += f"Total Backup size         {C2}{BOLD}{format_data(backup_size)}{RESET_ALL}\n"
        msg += f"Num Backups               {C2}{BOLD}{num_backups}{RESET_ALL}\n"
        msg += f"Backup interval            {C2}{BOLD}{format_time(self.backup_interval)}{RESET_ALL}\n"
        msg += f"Next backup                {C2}{BOLD}{dt_next_backup.strftime('%m/%d/%Y %H:%M')}"
        self.say(msg)

    # Perform the backup procedure
    def backup(self):
        self.say(f"{C1}{UNDERLINE}Backup Starting...{RESET_ALL}")
        self.execute("save-off")
        self.execute("save-all")

        # Wait for the save to complete. Arbitrary timeout period!
        time.sleep(3)
        
        # Backup the world to a zip file with a unique name
        backup_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_backup"
        shutil.make_archive(f"{os.path.join(self.backup_path, backup_name)}", 'zip', self.world_path)

        self.execute("save-on")
        self.say(f"{C1}{UNDERLINE}Backup Complete!{RESET_ALL}")

        print(f"Backup complete. {backup_name}.zip")

    def backup_loop(self):

        # Backup on startup
        print("Performing initial backup...")
        self.backup()
        self.say_info()

        backup_needed = False
        num_skipped = 0
        
        while True:
            # Wait until the backup interval has elapsed
            self.last_backup = time.time()
            while (time.time() - self.last_backup) < self.backup_interval:
                time.sleep(1)

                # Check the player count every second
                # If no one connects, there is no reason to backup
                if(self.get_player_count() != 0):
                    backup_needed = True
                    if(num_skipped > 0):
                        self.say(f"{C1}{UNDERLINE}Backup Agent Enabled\n{C2}{BOLD}{num_skipped}{RESET_ALL} backups have been skipped due to inactivity.")
                        num_skipped = 0

            # Check connection and attempt to reconect if necessarry
            if(not self.is_connected()):
                print(f"Lost connection, attempting to re-connect [{self.host}:{self.port}]")
                while(not self.connect()):
                    print("Failed to connect! Retrying in 3 seconds...")
                    time.sleep(3)
                    print(f"Attempting to re-connect to rcon server [{self.host}:{self.port}]")

                print("Connection established.")


            # Perform backup if needed
            if(backup_needed):
                print("Executing backup sequence...")
                self.backup()
                self.say_info()
                num_skipped = 0
            else:
                print("Backup skipped! No players online since last backup.")
                num_skipped+=1
            
            backup_needed = False
            

    def __init__(self):

        # Configuration
        print("---Minecraft Backup Agent---")
        if(not self.read_conf()):
            exit(1)

        # Connection
        print(f"Attempting to connect to rcon server [{self.host}:{self.port}]...", end="")
        while(not self.connect()):
            print("Fail.\nRetrying in 3 seconds...")
            time.sleep(3)
            print(f"Attempting to connect to rcon server [{self.host}:{self.port}]...", end="")

        # Startup message
        print("Connection established.")
        self.say(f"{C1}{UNDERLINE}Backup Agent Connected!")
       
        # Start the agent
        print("Starting Backup Agent...", end="")
        backup_thread = Thread(target=self.backup_loop, args=[])
        backup_thread.start()
        print("done.")


MCBackupAgent()