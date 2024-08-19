Instructions to Run Your Code on an Ubuntu EC2 Server

1. Activate the Python Virtual Environment:
Use the source command followed by the path to your virtual environment (myenv/bin/activate). 
This ensures that all the dependencies installed in this environment are used when running your script.
source myenv/bin/activate

2.Navigate to the Project Directory:
Use the cd command to change the current directory to your project folder, 7_ecom_scrapper-, where your code files are located.
cd 7_ecom_scrapper-

3.Open a Separate Terminal Session Using Screen:
Start a new screen session with the screen -S command followed by the name you want to give the session (e.g., mysession). 
Screen allows you to run processes independently of your current terminal session. You can detach from this session and return to 
it later without interrupting the running process.
screen -S mysession

4.Run Your Python Script:
Run your Python script (ecom2.py) using python3. This script will continue running in the screen session, even if you detach from it or disconnect from the server.
python3 ecom2.py

5.Detach from the Screen Session:
To detach from the screen and return to your main terminal, press Ctrl + A, then D. This key combination detaches you from the session, 
allowing the script to keep running in the background.

6.View Logged Data in Real-Time:
Use the tail -f command followed by the log file name (e.g., log_file_name.log) to display the live output of the log file. 
The -f flag allows you to follow the log file as it updates, so you can monitor the script's progress.
tail -f log_file_name.log

7.Open a File to View or Edit Data:
Open a file using the nano text editor by typing nano followed by the file name (e.g., file_name). 
This allows you to view or edit the contents of the file directly in the terminal.
nano file_name

8.List Files in the Current Directory:
Use the ls command to list all files and directories in the current directory. This helps you verify what files are present or locate the ones you want to interact with.
ls

9.Reattach to the Screen Session:
To reattach to your screen session, use the screen -r command followed by the session name (e.g., mysession). 
This reattaches you to the screen session where your code is running, allowing you to check on its progress or interact with the terminal session directly.
screen -r mysession
