# RouteBuddy Beacon

Experimental native iOS build of the RouteBuddy Beacon location transmitter.

Current features:
- Live GPS position
- Accuracy filtering
- Speed and course reporting
- Auto-follow map
- Track trail logging

- Beacon captures live GPS location and transmits a structured position report.

Architecture:

Beacon App
    uses QuodWords encoding

Related projects:
- QuodWords (location encoding system)
- RouteBuddyCore (shared utilities, future)
- RouteBuddyMaps (map stack, future)

This repository is part of the RouteBuddy ecosystem and supports the QuodWords geocoding project.

Status: early prototype.
