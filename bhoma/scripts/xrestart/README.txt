This is a set of scripts to restart X-Windows as a non-root user upon login.
This was written to work around a touchscreen driver issue that could only
be resolved by restarting X.

It uses the setuid flag on a file to make a c script executable as root to 
restart x.  Then it uses a python script to check against a timestamp and 
restart if it hasn't been touched recently.

You should copy this whole folder to a directory called .scripts in the user 
home directory.

The c script is a wrapper for restarting X using the service gdm command.  This
script gets compiled and the permissions changed so that it can be run from
any user but will execute as root. 

Compile it on your system using the following command (a binary is included
here as well):

 $ gcc restart-wrapper.c -o restart-wrapper -Wall

Then change the owner to root and the permissions using:
 
 $ sudo chown root:root restart-wrapper
 $ sudo chmod 4755 restart-wrapper

In order to ensure succses, make sure when you run:

 $ ls -l restart-wrapper

The line should look something like this (the important parts are that the
permission string on the left match exactly "-rwsr-xr-x" and the owner and
group are root.

-rwsr-xr-x 1 root root 8477 2010-08-18 09:55 restart-wrapper


The python script (assumed to be in the same directory) can then be run normally
and should do the correct thing without any prompting.  You can test this by
running the following command, which should restart xwindows.

 $ ./xrestart.py


In order to ensure that the python script is run upon login, edit the users
.profile file (which should be located at /home/<username>/.profile) and 
make the last line read:

/home/<username>/.scripts/

As a final test, make sure that when you restart the computer the file 
xbootlog.txt in this directory has an updated timestamp.