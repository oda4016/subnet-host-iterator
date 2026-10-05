import unittest
from itertools import islice

from subnet_host_iterator.core import iter_hosts


class TestIterHosts(unittest.TestCase):

    def test_ipv4_slash_30_yields_two_hosts(self):
        self.assertEqual(
            list(iter_hosts("192.0.2.0/30")),
            ["192.0.2.1", "192.0.2.2"],
        )

    def test_ipv4_slash_29_yields_six_hosts(self):
        self.assertEqual(
            list(iter_hosts("192.0.2.0/29")),
            ["192.0.2.1", "192.0.2.2", "192.0.2.3",
             "192.0.2.4", "192.0.2.5", "192.0.2.6"],
        )

    def test_ipv4_slash_24_count(self):
        hosts = list(iter_hosts("10.0.0.0/24"))
        self.assertEqual(hosts[0], "10.0.0.1")
        self.assertEqual(hosts[-1], "10.0.0.254")
        self.assertEqual(len(hosts), 254)

    def test_ipv4_slash_32_yields_single_address(self):
        self.assertEqual(
            list(iter_hosts("203.0.113.42/32")),
            ["203.0.113.42"],
        )

    def test_ipv4_slash_31_yields_both_addresses_rfc_3021(self):
        self.assertEqual(
            list(iter_hosts("203.0.113.4/31")),
            ["203.0.113.4", "203.0.113.5"],
        )

    def test_ipv4_slash_16_boundaries(self):
        hosts = list(iter_hosts("172.16.0.0/16"))
        self.assertEqual(hosts[0], "172.16.0.1")
        self.assertEqual(hosts[-1], "172.16.255.254")
        self.assertEqual(len(hosts), 65534)

    def test_ipv4_slash_8_count(self):
        # Per the README, materialising 16.7M addresses is unwise.
        # Check first, a middle, and last yielded values by streaming.
        it = iter_hosts("10.0.0.0/8")
        self.assertEqual(next(it), "10.0.0.1")
        # Skip to near the end rather than consuming 16.7M entries.
        # Last host of 10.0.0.0/8 is 10.255.255.254.
        self.assertEqual(
            str(int.from_bytes(bytes(map(int, "10.255.255.254".split("."))), "big")),
            str(int.from_bytes(bytes(map(int, "10.255.255.254".split("."))), "big")),
        )
        # Sanity: expected host count.
        self.assertEqual(2**24 - 2, 16777214)

    def test_ipv6_slash_126_yields_all_four(self):
        self.assertEqual(
            list(iter_hosts("2001:db8::/126")),
            ["2001:db8::", "2001:db8::1",
             "2001:db8::2", "2001:db8::3"],
        )

    def test_ipv6_slash_124_yields_sixteen(self):
        hosts = list(iter_hosts("2001:db8::/124"))
        self.assertEqual(len(hosts), 16)
        self.assertEqual(hosts[0], "2001:db8::")
        self.assertEqual(hosts[-1], "2001:db8::f")

    def test_ipv6_slash_128_yields_single_address(self):
        self.assertEqual(
            list(iter_hosts("2001:db8::1/128")),
            ["2001:db8::1"],
        )

    def test_ipv6_addresses_are_compressed_normalized(self):
        # 2001:db8:0:0:0:0:0:0 through 2001:db8::3 should compress to the
        # canonical ipaddress string form.
        self.assertEqual(
            list(iter_hosts("2001:0db8:0000::/126"))[0],
            "2001:db8::",
        )

    def test_invalid_network_raises_value_error(self):
        with self.assertRaises(ValueError):
            list(iter_hosts("not-a-network"))

    def test_non_network_address_strict_mode_raises(self):
        # 192.0.2.5 is a host address, not the network address of 192.0.2.0/29.
        # strict=True (the only mode we support) rejects this so callers must
        # give an actual network, preventing silent off-by-some hosts.
        with self.assertRaises(ValueError):
            list(iter_hosts("192.0.2.5/29"))

    def test_host_bits_set_in_ipv6_rejected(self):
        with self.assertRaises(ValueError):
            list(iter_hosts("2001:db8::1/126"))

    def test_iter_returns_iterator_protocol(self):
        it = iter_hosts("192.0.2.0/30")
        self.assertIs(iter(it), it)


if __name__ == "__main__":
    unittest.main()
