#! /usr/bin/python
# encoding: utf-8
import config
import os
import httplib

def _unicode(s):
    if isinstance(s, str):
        try:
            return s.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPError(400, "Non-utf8 argument")
    assert isinstance(s, unicode)
    return s

def _utf8(s):
    if isinstance(s, unicode):
        return s.encode("utf-8")
    assert isinstance(s, str)
    return s

sep = os.path.sep
sepsep = sep + sep


# /tag
# /tag/{tag}/this-week/
# /tag/{tag}/this-week/rating/
# /tag/{tag}/this-month/
# /artist
# /albums
# /playlists

import json
import urllib2
import re

cache = {}

class HeadRequest(urllib2.Request):
  def get_method(self):
      return "HEAD"

# stolen from tornado, there may be a more standart way but this works for me now
class HTTPHeaders(dict):
    """A dictionary that maintains Http-Header-Case for all keys."""
    def __setitem__(self, name, value):
        dict.__setitem__(self, self._normalize_name(name), value)

    def __getitem__(self, name):
        return dict.__getitem__(self, self._normalize_name(name))

    def _normalize_name(self, name):
        return "-".join([w.capitalize() for w in name.split("-")])

    @classmethod
    def parse(cls, headers_string):
        headers = cls()
        for line in headers_string.splitlines():
            if line:
                name, value = line.split(": ", 1)
                headers[name] = value
        return headers

class jBase:

  def normalize_obj(self, arr):
    ret = []
    for o in arr:
      k = {'id': -1, 'name':'-', 'type': 'folder', 'size':0}
      if 'sname' in o:
        name = o['sname']
      else:
        name = o['name']

      k.update(o)
      k['name'] = name
      ret.append(k)
      
    return ret

  def size(self, url):
    return self.head(url).get("Content-Length")

  def head(self, url):
    response = urllib2.urlopen(HeadRequest(url))
    try:
      return HTTPHeaders.parse("%s" % response.info())
    except Exception, e:
      print e


  def fetch(self, url):
      req = urllib2.Request(url)
      f = urllib2.urlopen(req)
      r = f.read()
      return json.loads(r)
    

class jTag(jBase):
  
  def __init__(self, dispatcher):
    self.dispatcher = dispatcher
    pass 

  def index(self):
    try:
      data = json.load(open('cachedtags.json'))
      return self.normalize_obj(data)
    except Exception, e:
      print e
      url = 'http://'+'api.jamendo.com/get2/id+name+weight+rating/tag/json?n=50&order=rating_desc'
      return self.normalize_obj(self.fetch(url))

  def list_time(self, tag):
    return self.normalize_obj([{'name': 'this-week'}, {'name': 'this-month'}, {'name': 'all-time'}])
  
  def list_albums(self, tag, ftime):
    if ftime == 'this-week':
      order = 'ratingweek'
    elif ftime == 'this-month':
      order = 'ratingmonth'
    else:
      order = 'rating'

    s = 'api.jamendo.com/get2/id+name+url+image+artist_name/album/json/?tag_idstr=%s&n=50&order=%s_desc' % (tag, order)
    albums = self.fetch('http://'+ s)
    for album in albums:
      key = '%s - %s' % (album['artist_name'], album['name'])
      album['sname'] = key
      cache[_utf8(key)] = album
    return self.normalize_obj(albums)

  def list_songs(self, tag, ftime, album):
    print 'list_songs',  tag, ftime, album
    if not album in cache:
      # try harder
      self.dispatcher.dispatch('/tag/%s/%s' % (tag, ftime))
      
    if not album in cache:
      print "album not in cache"
      return []
    s = 'api.jamendo.com/get2/id+name+stream+size/track/json?album_id=%s&n=100' % cache[album]['id']    
    objects = self.fetch('http://'+ s)
    for o in objects:
        o['type'] = 'file'
        o['sname'] = o['name'] + '.mp3'
        o['size'] = self.size(o['stream'])
    return self.normalize_obj(objects)

  def default(self):
   
    pathroot = [
      {'id':1, 'name':'tag', 'cls':jTag, 'action': 'get_all'},
    #  {id:2, name:'artist', virtual:1, cls:jArtist},
    #  {id:3, name:'albums', virtual:1, cls:jAlbums},
    #  {id:4, name:'playlists', virtual:1, cls:jPlaylist},
    ]

    return self.normalize_obj(pathroot)

  def song(self, tag, ftime, album, song):
    print 'songs', tag, ftime, album, song




routes = [
  {'route':r'/$', 'cls':jTag, 'action': 'default'},
  # /tag
  {'route':r'/tag$', 'cls':jTag, 'action': 'index'},
  # /tag/metal
  {'route':r'/tag/([^/]+$)', 'cls':jTag, 'action': 'list_time'},
  # /tag/metal/this-week
  {'route':r'/tag/([^/]+)/([^/]+$)', 'cls':jTag, 'action': 'list_albums'},
  # /tag/metal/this-week/{album}
  {'route':r'/tag/([^/]+)/([^/]+)/([^/]+$)', 'cls':jTag, 'action': 'list_songs'},
  # /tag/metal/this-week/{album}/{songs}
  {'route':r'/tag/([^/]+)/([^/]+)/([^/]+)/([^/]+$)', 'cls':jTag, 'action': 'song'},
]


class Path:

  def get_items(self, path='/'):
    return self.dispatch(path)

  def dispatch(self, path):
    path = path.replace('\\', '/')
    for route in routes:
      g = re.match(route['route'], path)
      if g:
        obj = route['cls'](self)
        action = getattr(obj, route['action'])
        return action(*g.groups())






if __name__ == '__main__':
#  for tag in jTag().get_all():
#    print tag['name']

  d = Path()
  
#  d.dispatch('/tag')
#  d.dispatch('/tag/metal')
#  albums = d.dispatch('/tag/metal/this-week')
  #print albums[0]['sname']
#  songs = d.dispatch('/tag/metal/this-week/%s' % albums[0]['sname'])
#  print songs[0]
  print d.dispatch("/tag/metal/this-month")
  print d.dispatch("/tag/metal/this-month/MaelStröM - Let's dance to ... forget")

  
#  d.dispatch('/tag/metal/this-week/foobar/1.mp3')


#  api = putio.Api(config.apikey, config.apisecret)
#  items = api.get_items(parent_id=24, limit=300)
#  for i in items:
#    print ">", i.id, i.name.encode('utf-8')

#  p = PathToId()
#  print p.find_item_by_path('/123/9')
#  p.invalidate_items_cache_by_path('/123/8')
#  p.invalidate_items_cache_by_path('/123/9')
#  p.invalidate_items_cache_by_path('/123')
#  print p.find_item_by_path('/123/9')
#  print p.find_item_by_path('/123')

#  p = PathToId()
#  #p.load_items('/x', 11156055)
#  p.load_items()
#  print "============================="
#  print p.find_item_by_path('/x/y/z/rtorrent.log')
#  print p.find_item_by_path('/x/y/z')
  #p.find_item_by_path('/x/y/z')
#  s = 'çöğüışIĞÜÇÖ'.decode('utf-8')
#  print s, type(s)


