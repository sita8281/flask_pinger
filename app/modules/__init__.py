from .icmp_daemon import ICMPdaemon
from .nas_daemon import NASdaemon
from .sw_dump import DumperSW
from .forward_gateway import ForwardGatewayServer
from .web_session_maker import SessionMaker

dumper_sw = DumperSW()
pinger = ICMPdaemon()
nas_poller = NASdaemon()
vpn_gateway = ForwardGatewayServer()
sessions_online = SessionMaker()

pinger.start()
nas_poller.start()
vpn_gateway.start()
sessions_online.start()


