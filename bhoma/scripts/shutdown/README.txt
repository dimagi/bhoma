The c script is a wrapper for shutting down the computer.  This
script gets compiled and the permissions changed so that it can be run from
any user but will execute as root. 

Compile it on your system using the following command (a binary is included
here as well):

 $ gcc shutdown.c -o shutdown-wrapper -Wall

Then change the owner to root and the permissions using:
 
 $ sudo chown root:root shutdown-wrapper
 $ sudo chmod 4755 shutdown-wrapper

In order to ensure success, make sure when you run:

 $ ls -l shutdown-wrapper

The line should look something like this (the important parts are that the
permission string on the left match exactly "-rwsr-xr-x" and the owner and
group are root.

-rwsr-xr-x 1 root root 8477 2010-08-18 09:55 shutdown-wrapper


The script (assumed to be in this directory) can then be run normally.