#!/usr/bin/env python
# $Id: basic_ftpd.py 569 2009-04-04 00:17:43Z billiejoex $

"""A basic FTP server which uses a DummyAuthorizer for managing 'virtual
users', setting a limit for incoming connections.
"""

import os

#from pyftpdlib
import ftpserver
import urllib2
import jamendoapi
import config
import time

class HttpFD(object):

    def __init__(self, apifile, bucket, obj, mode):
        self.apifile = apifile
        self.download_url = apifile['stream']
        self.bucket = bucket
        self.name = obj
        self.mode = mode
        self.closed = False
        self.total_size = None
        self.seekpos = None

        self.read_size = 0
        # speed...
        self.read_bytes = 128 * 1024 # 128kb per iteration
        self.buffer = ''
        self.req = None
        self.fd = None

        # gets total size
        req = urllib2.Request(self.download_url)
        f = urllib2.urlopen(req)
        self.total_size = f.headers.get('Content-Length')


    def write(self, data):
        raise OSError(1, 'Operation not permitted')
        # self.temp_file.write(data)

    def close(self):
        return

    def __read(self, size=65536):
        c =  self.buffer
        self.buffer = ''
        return c

    def read(self, size=65536):
        if self.req == None:
            self.req = urllib2.Request(self.download_url)

        if self.seekpos:
            self.req.headers['Range'] = 'bytes=%s-' % (self.seekpos)

        if self.read_size > self.total_size:
          return

        self.read_size = self.read_size + self.read_bytes + 1
        if not self.fd:
            self.fd = urllib2.urlopen(self.req)

        return self.fd.read(1024)


    def seek(self, frombytes, **kwargs):
        print ">>>>>>>>>> seek"
        self.seekpos = frombytes
        return


# ....

api = None


class HttpFS(ftpserver.AbstractedFS):

    def __init__(self):
        self.root = None
        self.cwd = '/'
        self.rnfr = None
        self.dirlistcache = {}

    def open(self, filename, mode):
        print "filename: ", filename

        if filename in self.dirlistcache:
          apifile = self.dirlistcache[filename]
        else:
          if filename == os.path.sep:
            # items = operations.api.get_items()
            # this is not a file its a directory
            # raise OSError(1, 'This is a directory')
            raise IOError(1, 'This is a directory')
          else:
            apifile = self._getitem(filename)


        #
        if apifile['type'] == 'folder':
          raise IOError(1, 'This is a directory')

        #
        return HttpFD(apifile, None, filename, mode)

    def chdir(self, path):
        self.cwd = path.decode('utf-8').encode('utf-8')

    def mkdir(self, path):
      raise OSError(1, 'Operation not permitted')


    def listdir(self, path):
        ret = []

        try:
          items = operations.api.get_items(path)
        except:
          return []

        for i in items:
          ret.append(i['name'])

        return ret

    def remove_from_cache(self, path):
      raise OSError(1, 'Operation not permitted')

    def rmdir(self, path):
      raise OSError(1, 'Operation not permitted')

    def remove(self, path):
      raise OSError(1, 'Operation not permitted')
    
    def rename(self, src, dst):
      raise OSError(1, 'Operation not permitted')


    def isfile(self, path):
        return not self.isdir(path)

    def islink(self, path):
        return False

    def isdir(self, path):
      if path == os.path.sep:
        return True
      apifile = self._getitem(path)
      if not apifile:
        raise OSError(2, 'No such file or directory')
      if apifile['type'] == 'folder':
        return True
      else:
        return False

    def getsize(self, path):
      print ">>>>>>>>>>>>> GETSIZE"
      apifile = self._getitem(path)
      if not apifile:
        raise OSError(1, 'No such file or directory')
      print apifile
      print "filesize :", apifile['size']
      return long(apifile['size'])
        #return self.stat(path).st_size

    def getmtime(self, path):
        print "mtime"
        return self.stat(path).st_mtime

    def realpath(self, path):
        return path

    def lexists(self, path):
      print "lexists"
      apifile = self._getitem(path)
      if not apifile:
        raise OSError(2, 'No such file or directory')
      return apifile


    def _getitem(self, filename):
        print "filename: ", filename

        if filename in self.dirlistcache:
          apifile = self.dirlistcache[filename]
        else:
          if filename == os.path.sep:
            # items = operations.api.get_items()
            return False
          else:

            basepath, f = os.path.split(filename)
            items = operations.api.get_items(basepath)
            for item in items:
              if jamendoapi._utf8(item['name']) == f:
                apifile = item
            self.dirlistcache[filename] = apifile

        return apifile #.get_download_url()


    def stat(self, path):
        print ">>>>>> stat:", path
        apifile = self._getitem(path)

        return os.stat_result((666, 0L, 0L, 0, 0, 0, apifile.size, 0, 0, 0))

    exists = lexists
    lstat = stat

    def validpath(self, path):
        return True

    def format_list_items(self, items):
      for item in items:
        if item['type'] == 'folder':
          s = 'drwxrwxrwx 1 %s group %8s Jan 01 00:00 %s\r\n' % ('aaa', 0, item['name'])
        else:
          s = '-rw-rw-rw- 1 %s group %8s %s %s\r\n' % ('aaa', item['size'], time.strftime("%b %d %H:%M"), item['name'])
        yield s.encode('utf-8')

    def get_list_dir(self, path):
        try:
          items = operations.api.get_items(path)
        except:
          return self.format_list_items([])
        return self.format_list_items(items)

    def format_mlsx(self, basedir, listing, perms, facts, ignore_err=True):

      # find item in cache...
      if basedir in self.dirlistcache:
        fnd = self.dirlistcache[basedir]
        # TOdo; cache ??? 
        try:
          items = operations.api.get_items(basedir)
        except Exception, e:
          items = []
          print e
      else:
          items = operations.api.get_items(basedir)

      print "======================== items =================="
      print items
      print "================================================="
      
      c = 0
      s = ''
      for i in items:
          c = c + 1

          type = 'type=file;'

          if 'type' in facts:
            if i['type'] == 'folder':
              type = 'type=dir;'

          if 'size' in facts:
              size = 'size=%s;' % i['size']  # file size

          ln = "%s%sperm=r;modify=20071029155301;unique=11150051; %s\r\n" % (type, size, i['name'])

          if basedir== os.path.sep:
            key = '/%s' % (jamendoapi._utf8(i['name']))
          else:
            key = '%s/%s' % (jamendoapi._utf8(basedir), jamendoapi._utf8(i['name']))

          self.dirlistcache[key] = i
          print 'key:', key

          yield ln.encode('utf-8')




class HttpOperations(object):
    '''Storing connection object'''
    def __init__(self):
        self.connection = None
        self.username = None

    def authenticate(self, username, password):
        self.username = username
        self.password = password
        self.api = jamendoapi.Path()
        return True

    def __repr__(self):
        return self.connection

operations = HttpOperations()


class HttpAuthorizer(ftpserver.DummyAuthorizer):
    '''FTP server authorizer. Logs the users into Putio Cloud
Files and keeps track of them.
'''
    users = {}

    def validate_authentication(self, username, password):
        try:
            operations.authenticate(username, password)
            return True
        except Exception, e:
            print e
            return False

    def has_user(self, username):
        return username != 'anonymous'

    def has_perm(self, username, perm, path=None):
        return True

    def get_perms(self, username):
        return 'lrdw'

    def get_home_dir(self, username):
        return os.sep

    def get_msg_login(self, username):
        return 'Welcome %s' % username

    def get_msg_quit(self, username):
        return 'Goodbye %s' % username



def main():

      ftp_handler = ftpserver.FTPHandler
      ftp_handler.authorizer = HttpAuthorizer()
      ftp_handler.abstracted_fs = HttpFS
      address = (config.ip_address, 2121 )
      ftpd = ftpserver.FTPServer(address, ftp_handler)
      ftpd.serve_forever()


if __name__ == '__main__':
    main()

