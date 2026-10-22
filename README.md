# subnet_host_iterator

Yield every usable host address in an IPv4 or IPv6 CIDR subnet, skipping network and broadcast addresses where the relevant RFC says to.

```python
from subnet_host_iterator import iter_hosts

for host in iter_hosts("192.0.2.0/30"):
    print(host)
# 192.0.2.1
# 192.0.2.2

for host in iter_hosts("2001:db8::/126"):
    print(host)
# 2001:db8::
# 2001:db8::1
# 2001:db8::2
# 2001:db8::3
```

The single exported name is `iter_hosts`, a function taking one CIDR string and returning an iterator of address strings.

## Why this exists

Walking a subnet's hosts is the kind of thing people keep reinventing with `ipaddress` plus a hand-rolled loop that forgets the broadcast address, or mishandles `/31`, or skips the wrong end of an IPv6 block. This library is a small, correct, dependency-free boundary: one function that knows the three IPv4 special cases (`/31` per RFC 3021, `/32`, and everything else) and the IPv6 rule (RFC 4291 says all addresses in the block are valid hosts, so nothing is skipped).

The trade-off: the function yields strings, not `ipaddress.IPv4Address`/`IPv6Address` objects. That keeps the public surface tiny and lets callers decide whether they want objects (wrap with `ipaddress.ip_address(host)`) or plain strings for logging, configuration files, or socket calls. If you need objects directly, this is the wrong library and that is fine.

## The awkward edges

- **IPv4 `/31`**: both addresses are returned, not just one. This is per RFC 3021 (point-to-point links have no broadcast). If you expected one host, that is the surprise.
- **IPv4 `/32`**: the single address is returned as a host. There is no broadcast to skip on a host route.
- **IPv6 any prefix**: the network address (all-zero host bits) is returned as a host. IPv6 has no broadcast; per RFC 4291 every address in the block is a valid host.
- **Strict mode only**: `iter_hosts("192.0.2.5/29")` raises `ValueError`. The input must be a true network address (host bits zero). This prevents silent off-by-N iteration when a caller passes a host address by mistake.
- **Large prefixes**: `10.0.0.0/8` yields ~16.7 million addresses. The iterator is lazy, but materialising the whole thing with `list()` will allocate that much. Stream it.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

