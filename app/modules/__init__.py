from .icmp_daemon import ICMPdaemon


pinger = ICMPdaemon()
pinger.start()