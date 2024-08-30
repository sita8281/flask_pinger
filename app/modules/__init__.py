from .icmp_daemon import ICMPdaemon
from .web_session_maker import SessionMaker


sessions_online = SessionMaker()
pinger = ICMPdaemon()

pinger.start()
sessions_online.start()