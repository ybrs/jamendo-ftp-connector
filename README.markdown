An FTP interface to [Jamendo](http://www.jamendo.com/) music.
=============================================================

If you are on windows and install [ftpdrive](http://www.killprog.com/fdrve.html) too and mount it as a harddrive, you suddenly can access a huge disk with tons of music. (see it in action [vimeo](http://vimeo.com/19317287) )


Instructions:
=============

for *nix users: 
------------------
+ install python 2.6.6 (haven't tested in other versions)
+ just download everything in a folder, and run 
     python jamendo-ftp-connector.py

+ from your favorite ftp client login to localhost port 2121. (enter anything for your username and password)
	 
for windows users:
------------------
+ install python 2.6.6 ( http://www.python.org/download/releases/2.6.6/ ) - i don't know if other versions will work or not. 
+ download everything to one folder. double click putio-ftp-connector.py . (when you run connector it will say something like Serving FTP on 192.168.1.225:2121, 192.168.1.255 is your local ip address)
      if you see an ipv6 kind adress or can't see an ip address when it starts edit config.py  and enter your ipadress there.

+ download filezilla from http://filezilla-project.org/download.php?type=client and enter your local ip address to server and enter 2121 to port. (you can enter anything as your user name and password).
+ hit connect, if everything goes well you will see your files.

