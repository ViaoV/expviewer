This sets up an experience logging script that logs rank levels over time and provides a web app to view the data.


# Installation

This assumes you have python installed:

Installing Python: https://realpython.com/installing-python/

1. Download the files or clone the repo

2. copy the explog.lic into your lich/scripts folder

3. copy the expview.py into your lich folder

4. The explog script needs to be trusted to work, because it uses sqlite3. You shouldnt trust things blindly. The code is straight forward and documented so click the link above for the explog.lic and have a look through it. To trust the script run ```;trust explog``` from inside your FE.
5. To get the best use you should probably add it to the auto start with ```;autostart add explog```

6. The data is written every 15-30 mintues (depending on script pauses). It is also written when the script is killed so if you want some data run it for a few minutes, kill it ```;k explog```, run it again ```;explog```,  wait another few minutes and kill it. Or just let it run forawhile and collect and write data normally. This should create a file in your lich folder called explog.db. It is important that the expview.py file and this explog.db     file are in the same directory.

7. To view the data you need Flask for python, install that by running ```pip install flask``` in the terminal or check out http://flask.pocoo.org/docs/1.0/installation/

8. Launch the app with ```python expview.py```. This should run the server and open a web browser to http://localhost:5000




