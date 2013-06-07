from chimera.util.position import Position

import urllib2
import re





def SsODNetlookup(target):
    coords=urllib2.urlopen("http://vo.imcce.fr/webservices/ssodnet/resolver?mime=ascii&coord=2D&name="+target).read()
    scoords=coords.split("\n")
    success=0
    for line in scoords:
      m=re.match('# flag:\D*(\d)+',scoords[0])
      if m:
        flag=m.group()[-1]
        success=(flag=='1')
    if (not success):
      return None
    for line in scoords:
      if len(line.strip()):
        m=re.match('^#.+',line.strip())
        if (not m):
          res=line.split("|")
    if (len(res) < 8):
      return None
    return Position.fromRaDec(res[-2],res[-1])
