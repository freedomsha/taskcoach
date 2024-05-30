
from twisted.application import service
from buildslave.bot import BuildSlave

basedir = '.'
host = 'jeromelaheurte.net'
port = 9989
slavename = 'Ubuntu10'
passwd = file('.passwd', 'rb').readlines()[0].strip()
keepalive = 600
usepty = 1
umask = None

application = service.Application('buildslave')
s = BuildSlave(host, port, slavename, passwd, basedir, keepalive, usepty,
               umask=umask)
s.setServiceParent(application)

