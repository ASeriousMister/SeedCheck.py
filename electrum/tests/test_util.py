from decimal import Decimal

from electrum.util import (format_satoshis, format_fee_satoshis, parse_URI,
                           is_hash256_str, chunks, is_ip_address, list_enabled_bits,
                           format_satoshis_plain, is_private_netaddress, is_hex_str,
                           is_integer, is_non_negative_integer, is_int_or_float,
                           is_non_negative_int_or_float)

from . import ElectrumTestCase


class TestUtil(ElectrumTestCase):

    def test_format_satoshis(self):
        self.assertEqual("0.00001234", format_satoshis(1234))

    def test_format_satoshis_negative(self):
        self.assertEqual("-0.00001234", format_satoshis(-1234))

    def test_format_satoshis_to_mbtc(self):
        self.assertEqual("0.01234", format_satoshis(1234, decimal_point=5))

    def test_format_satoshis_decimal(self):
        self.assertEqual("0.00001234", format_satoshis(Decimal(1234)))

    def test_format_satoshis_msat_resolution(self):
        self.assertEqual("45831276.",    format_satoshis(Decimal("45831276"), decimal_point=0))
        self.assertEqual("45831276.",    format_satoshis(Decimal("45831275.748"), decimal_point=0))
        self.assertEqual("45831275.75", format_satoshis(Decimal("45831275.748"), decimal_point=0, precision=2))
        self.assertEqual("45831275.748", format_satoshis(Decimal("45831275.748"), decimal_point=0, precision=3))

        self.assertEqual("458312.76",    format_satoshis(Decimal("45831276"), decimal_point=2))
        self.assertEqual("458312.76",    format_satoshis(Decimal("45831275.748"), decimal_point=2))
        self.assertEqual("458312.7575", format_satoshis(Decimal("45831275.748"), decimal_point=2, precision=2))
        self.assertEqual("458312.75748", format_satoshis(Decimal("45831275.748"), decimal_point=2, precision=3))

        self.assertEqual("458.31276", format_satoshis(Decimal("45831276"), decimal_point=5))
        self.assertEqual("458.31276", format_satoshis(Decimal("45831275.748"), decimal_point=5))
        self.assertEqual("458.3127575", format_satoshis(Decimal("45831275.748"), decimal_point=5, precision=2))
        self.assertEqual("458.31275748", format_satoshis(Decimal("45831275.748"), decimal_point=5, precision=3))

    def test_format_fee_float(self):
        self.assertEqual("1.7", format_fee_satoshis(1700/1000))

    def test_format_fee_decimal(self):
        self.assertEqual("1.7", format_fee_satoshis(Decimal("1.7")))

    def test_format_fee_precision(self):
        self.assertEqual("1.666",
                         format_fee_satoshis(1666/1000, precision=6))
        self.assertEqual("1.7",
                         format_fee_satoshis(1666/1000, precision=1))

    def test_format_satoshis_whitespaces(self):
        self.assertEqual("     0.0001234 ", format_satoshis(12340, whitespaces=True))
        self.assertEqual("     0.00001234", format_satoshis(1234, whitespaces=True))
        self.assertEqual("     0.45831275", format_satoshis(Decimal("45831275."), whitespaces=True))
        self.assertEqual("     0.45831275   ", format_satoshis(Decimal("45831275."), whitespaces=True, precision=3))
        self.assertEqual("     0.458312757  ", format_satoshis(Decimal("45831275.7"), whitespaces=True, precision=3))
        self.assertEqual("     0.45831275748", format_satoshis(Decimal("45831275.748"), whitespaces=True, precision=3))

    def test_format_satoshis_whitespaces_negative(self):
        self.assertEqual("    -0.0001234 ", format_satoshis(-12340, whitespaces=True))
        self.assertEqual("    -0.00001234", format_satoshis(-1234, whitespaces=True))

    def test_format_satoshis_diff_positive(self):
        self.assertEqual("+0.00001234", format_satoshis(1234, is_diff=True))
        self.assertEqual("+456789.00001234", format_satoshis(45678900001234, is_diff=True))

    def test_format_satoshis_diff_negative(self):
        self.assertEqual("-0.00001234", format_satoshis(-1234, is_diff=True))
        self.assertEqual("-456789.00001234", format_satoshis(-45678900001234, is_diff=True))
        
    def test_format_satoshis_add_thousands_sep(self):
        self.assertEqual("178 890 000.", format_satoshis(Decimal(178890000), decimal_point=0, add_thousands_sep=True))
        self.assertEqual("458 312.757 48", format_satoshis(Decimal("45831275.748"), decimal_point=2, add_thousands_sep=True, precision=5))
        # is_diff
        self.assertEqual("+4 583 127.574 8", format_satoshis(Decimal("45831275.748"), decimal_point=1, is_diff=True, add_thousands_sep=True, precision=4))
        self.assertEqual("+456 789 112.004 56", format_satoshis(Decimal("456789112.00456"), decimal_point=0, is_diff=True, add_thousands_sep=True, precision=5)) 
        self.assertEqual("-0.000 012 34", format_satoshis(-1234, is_diff=True, add_thousands_sep=True)) 
        self.assertEqual("-456 789.000 012 34", format_satoshis(-45678900001234, is_diff=True, add_thousands_sep=True))
        # num_zeros
        self.assertEqual("-456 789.123 400", format_satoshis(-45678912340000, num_zeros=6, add_thousands_sep=True))
        self.assertEqual("-456 789.123 4", format_satoshis(-45678912340000, num_zeros=2, add_thousands_sep=True))
        # whitespaces
        self.assertEqual("      1 432.731 11", format_satoshis(143273111, decimal_point=5, add_thousands_sep=True, whitespaces=True))
        self.assertEqual("      1 432.731   ", format_satoshis(143273100, decimal_point=5, add_thousands_sep=True, whitespaces=True))
        self.assertEqual(" 67 891 432.731   ", format_satoshis(6789143273100, decimal_point=5, add_thousands_sep=True, whitespaces=True))
        self.assertEqual("       143 273 100.", format_satoshis(143273100, decimal_point=0, add_thousands_sep=True, whitespaces=True))
        self.assertEqual(" 6 789 143 273 100.", format_satoshis(6789143273100, decimal_point=0, add_thousands_sep=True, whitespaces=True))
        self.assertEqual("56 789 143 273 100.", format_satoshis(56789143273100, decimal_point=0, add_thousands_sep=True, whitespaces=True))

    def test_format_satoshis_plain(self):
        self.assertEqual("0.00001234", format_satoshis_plain(1234))

    def test_format_satoshis_plain_decimal(self):
        self.assertEqual("0.00001234", format_satoshis_plain(Decimal(1234)))

    def test_format_satoshis_plain_to_mbtc(self):
        self.assertEqual("0.01234", format_satoshis_plain(1234, decimal_point=5))

    def _do_test_parse_URI(self, uri, expected):
        result = parse_URI(uri)
        self.assertEqual(expected, result)

    def test_parse_URI_address(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma'})

    def test_parse_URI_only_address(self):
        self._do_test_parse_URI('15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma'})


    def test_parse_URI_address_label(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?label=electrum%20test',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'label': 'electrum test'})

    def test_parse_URI_address_message(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?message=electrum%20test',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'message': 'electrum test', 'memo': 'electrum test'})

    def test_parse_URI_address_amount(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?amount=0.0003',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'amount': 30000})

    def test_parse_URI_address_request_url(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?r=http://domain.tld/page?h%3D2a8628fc2fbe',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'r': 'http://domain.tld/page?h=2a8628fc2fbe'})

    def test_parse_URI_ignore_args(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?test=test',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'test': 'test'})

    def test_parse_URI_multiple_args(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?amount=0.00004&label=electrum-test&message=electrum%20test&test=none&r=http://domain.tld/page',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'amount': 4000, 'label': 'electrum-test', 'message': u'electrum test', 'memo': u'electrum test', 'r': 'http://domain.tld/page', 'test': 'none'})

    def test_parse_URI_no_address_request_url(self):
        self._do_test_parse_URI('bitcoin:?r=http://domain.tld/page?h%3D2a8628fc2fbe',
                                {'r': 'http://domain.tld/page?h=2a8628fc2fbe'})

    def test_parse_URI_invalid_address(self):
        self.assertRaises(BaseException, parse_URI, 'bitcoin:invalidaddress')

    def test_parse_URI_invalid(self):
        self.assertRaises(BaseException, parse_URI, 'notbitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma')

    def test_parse_URI_parameter_polution(self):
        self.assertRaises(Exception, parse_URI, 'bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?amount=0.0003&label=test&amount=30.0')

    def test_is_hash256_str(self):
        self.assertTrue(is_hash256_str('09a4c03e3bdf83bbe3955f907ee52da4fc12f4813d459bc75228b64ad08617c7'))
        self.assertTrue(is_hash256_str('2A5C3F4062E4F2FCCE7A1C7B4310CB647B327409F580F4ED72CB8FC0B1804DFA'))
        self.assertTrue(is_hash256_str('00' * 32))

        self.assertFalse(is_hash256_str('00' * 33))
        self.assertFalse(is_hash256_str('qweqwe'))
        self.assertFalse(is_hash256_str(None))
        self.assertFalse(is_hash256_str(7))

    def test_is_hex_str(self):
        self.assertTrue(is_hex_str('09a4'))
        self.assertTrue(is_hex_str('abCD'))
        self.assertTrue(is_hex_str('2A5C3F4062E4F2FCCE7A1C7B4310CB647B327409F580F4ED72CB8FC0B1804DFA'))
        self.assertTrue(is_hex_str('00' * 33))

        self.assertFalse(is_hex_str('0x09a4'))
        self.assertFalse(is_hex_str('2A 5C3F'))
        self.assertFalse(is_hex_str(' 2A5C3F'))
        self.assertFalse(is_hex_str('2A5C3F '))
        self.assertFalse(is_hex_str('000'))
        self.assertFalse(is_hex_str('123'))
        self.assertFalse(is_hex_str('0x123'))
        self.assertFalse(is_hex_str('qweqwe'))
        self.assertFalse(is_hex_str(b'09a4'))
        self.assertFalse(is_hex_str(b'\x09\xa4'))
        self.assertFalse(is_hex_str(None))
        self.assertFalse(is_hex_str(7))
        self.assertFalse(is_hex_str(7.2))

    def test_is_integer(self):
        self.assertTrue(is_integer(7))
        self.assertTrue(is_integer(0))
        self.assertTrue(is_integer(-1))
        self.assertTrue(is_integer(-7))

        self.assertFalse(is_integer(Decimal("2.0")))
        self.assertFalse(is_integer(Decimal(2.0)))
        self.assertFalse(is_integer(Decimal(2)))
        self.assertFalse(is_integer(0.72))
        self.assertFalse(is_integer(2.0))
        self.assertFalse(is_integer(-2.0))
        self.assertFalse(is_integer('09a4'))
        self.assertFalse(is_integer('2A5C3F4062E4F2FCCE7A1C7B4310CB647B327409F580F4ED72CB8FC0B1804DFA'))
        self.assertFalse(is_integer('000'))
        self.assertFalse(is_integer('qweqwe'))
        self.assertFalse(is_integer(None))

    def test_is_non_negative_integer(self):
        self.assertTrue(is_non_negative_integer(7))
        self.assertTrue(is_non_negative_integer(0))

        self.assertFalse(is_non_negative_integer(Decimal("2.0")))
        self.assertFalse(is_non_negative_integer(Decimal(2.0)))
        self.assertFalse(is_non_negative_integer(Decimal(2)))
        self.assertFalse(is_non_negative_integer(0.72))
        self.assertFalse(is_non_negative_integer(2.0))
        self.assertFalse(is_non_negative_integer(-2.0))
        self.assertFalse(is_non_negative_integer(-1))
        self.assertFalse(is_non_negative_integer(-7))
        self.assertFalse(is_non_negative_integer('09a4'))
        self.assertFalse(is_non_negative_integer('2A5C3F4062E4F2FCCE7A1C7B4310CB647B327409F580F4ED72CB8FC0B1804DFA'))
        self.assertFalse(is_non_negative_integer('000'))
        self.assertFalse(is_non_negative_integer('qweqwe'))
        self.assertFalse(is_non_negative_integer(None))

    def test_is_int_or_float(self):
        self.assertTrue(is_int_or_float(7))
        self.assertTrue(is_int_or_float(0))
        self.assertTrue(is_int_or_float(-1))
        self.assertTrue(is_int_or_float(-7))
        self.assertTrue(is_int_or_float(0.72))
        self.assertTrue(is_int_or_float(2.0))
        self.assertTrue(is_int_or_float(-2.0))

        self.assertFalse(is_int_or_float(Decimal("2.0")))
        self.assertFalse(is_int_or_float(Decimal(2.0)))
        self.assertFalse(is_int_or_float(Decimal(2)))
        self.assertFalse(is_int_or_float('09a4'))
        self.assertFalse(is_int_or_float('2A5C3F4062E4F2FCCE7A1C7B4310CB647B327409F580F4ED72CB8FC0B1804DFA'))
        self.assertFalse(is_int_or_float('000'))
        self.assertFalse(is_int_or_float('qweqwe'))
        self.assertFalse(is_int_or_float(None))

    def test_is_non_negative_int_or_float(self):
        self.assertTrue(is_non_negative_int_or_float(7))
        self.assertTrue(is_non_negative_int_or_float(0))
        self.assertTrue(is_non_negative_int_or_float(0.0))
        self.assertTrue(is_non_negative_int_or_float(0.72))
        self.assertTrue(is_non_negative_int_or_float(2.0))

        self.assertFalse(is_non_negative_int_or_float(-1))
        self.assertFalse(is_non_negative_int_or_float(-7))
        self.assertFalse(is_non_negative_int_or_float(-2.0))
        self.assertFalse(is_non_negative_int_or_float(Decimal("2.0")))
        self.assertFalse(is_non_negative_int_or_float(Decimal(2.0)))
        self.assertFalse(is_non_negative_int_or_float(Decimal(2)))
        self.assertFalse(is_non_negative_int_or_float('09a4'))
        self.assertFalse(is_non_negative_int_or_float('2A5C3F4062E4F2FCCE7A1C7B4310CB647B327409F580F4ED72CB8FC0B1804DFA'))
        self.assertFalse(is_non_negative_int_or_float('000'))
        self.assertFalse(is_non_negative_int_or_float('qweqwe'))
        self.assertFalse(is_non_negative_int_or_float(None))

    def test_chunks(self):
        self.assertEqual([[1, 2], [3, 4], [5]],
                         list(chunks([1, 2, 3, 4, 5], 2)))
        self.assertEqual([], list(chunks(b'', 64)))
        self.assertEqual([b'12', b'34', b'56'],
                         list(chunks(b'123456', 2)))
        with self.assertRaises(ValueError):
            list(chunks([1, 2, 3], 0))

    def test_list_enabled_bits(self):
        self.assertEqual((0, 2, 3, 6), list_enabled_bits(77))
        self.assertEqual((), list_enabled_bits(0))

    def test_is_ip_address(self):
        self.assertTrue(is_ip_address("127.0.0.1"))
        #self.assertTrue(is_ip_address("127.000.000.1"))  # disabled as result differs based on python version
        self.assertTrue(is_ip_address("255.255.255.255"))
        self.assertFalse(is_ip_address("255.255.256.255"))
        self.assertFalse(is_ip_address("123.456.789.000"))
        self.assertTrue(is_ip_address("2001:0db8:0000:0000:0000:ff00:0042:8329"))
        self.assertTrue(is_ip_address("2001:db8:0:0:0:ff00:42:8329"))
        self.assertTrue(is_ip_address("2001:db8::ff00:42:8329"))
        self.assertFalse(is_ip_address("2001:::db8::ff00:42:8329"))
        self.assertTrue(is_ip_address("::1"))
        self.assertFalse(is_ip_address("2001:db8:0:0:g:ff00:42:8329"))
        self.assertFalse(is_ip_address("lol"))
        self.assertFalse(is_ip_address(":@ASD:@AS\x77\x22\xff¬!"))

    def test_is_private_netaddress(self):
        self.assertTrue(is_private_netaddress("127.0.0.1"))
        self.assertTrue(is_private_netaddress("127.5.6.7"))
        self.assertTrue(is_private_netaddress("::1"))
        self.assertTrue(is_private_netaddress("[::1]"))
        self.assertTrue(is_private_netaddress("localhost"))
        self.assertTrue(is_private_netaddress("localhost."))
        self.assertFalse(is_private_netaddress("[::2]"))
        self.assertFalse(is_private_netaddress("2a00:1450:400e:80d::200e"))
        self.assertFalse(is_private_netaddress("[2a00:1450:400e:80d::200e]"))
        self.assertFalse(is_private_netaddress("8.8.8.8"))
        self.assertFalse(is_private_netaddress("example.com"))
