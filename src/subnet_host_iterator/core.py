"""Yield usable host addresses from an IPv4 or IPv6 subnet.

Design decisions (stated plainly so the tests can pin them down):

* IPv4: for prefixes strictly shorter than /31, the network and broadcast
  addresses are skipped (RFC 791). For /31 networks, both addresses are
  returned unchanged per RFC 3021, which defines /31 as a point-to-point link
  with no broadcast. For /32, the single address is returned. These three
  cases are the only IPv4 prefixes where skipping the broadcast would be
  wrong, so they are special-cased explicitly rather than papered over with a
  generic rule.

* IPv6: per RFC 4291, all 128 bits of the network address may be used as a
  host address ("In IPv6, all 0's and all 1's are legal values for any field
  in an address"). Therefore no addresses are skipped for any IPv6 prefix
  length, including /128 which yields the single address.

* The iterator yields strings, not ipaddress objects, to keep the public
  surface narrow and dependency-free. Callers who need objects can wrap with
  ipaddress.ip_address().
"""

from __future__ import annotations

import ipaddress
from collections.abc import Iterator


def iter_hosts(network: str) -> Iterator[str]:
    """Yield every usable host address in *network* as a string.

    *network* is a network string in CIDR notation (e.g. "192.0.2.0/30",
    "2001:db8::/126"). Both IPv4 and IPv6 are supported.

    See the module docstring for the exact rule on which addresses are skipped
    for each prefix length.
    """
    net = ipaddress.ip_network(network, strict=True)
    num_addresses = net.num_addresses

    # /0 is a special case: the first address of 0.0.0.0/0 or ::/0 is the
    # network address (all zeros). For IPv4 we skip it; for IPv6 we keep it.
    # In both families the very last address is the broadcast/reserved address;
    # for IPv4 we skip it, for IPv6 we keep it. This falls out of the family
    # checks below.

    if isinstance(net, ipaddress.IPv4Network):
        if num_addresses == 1:
            # /32: the single address is a host address.
            yield str(net.network_address)
            return
        if net.prefixlen == 31:
            # RFC 3021: both addresses of a /31 are usable host addresses on a
            # point-to-point link; there is no broadcast to skip.
            yield str(net.network_address)
            yield str(net.network_address + 1)
            return
        # Every other IPv4 prefix: skip network (first) and broadcast (last).
        # The range() bounds compute inclusive-start, exclusive-end in terms of
        # integer address values.
        first = int(net.network_address) + 1
        last = int(net.broadcast_address)
        yield from (str(ipaddress.IPv4Address(i)) for i in range(first, last))
        return

    # IPv6: no addresses are skipped for any prefix length per RFC 4291.
    first = int(net.network_address)
    last = first + num_addresses
    yield from (str(ipaddress.IPv6Address(i)) for i in range(first, last))
