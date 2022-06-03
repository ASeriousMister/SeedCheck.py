#!/usr/bin/env python3
# create a BIP70 payment request signed with a certificate
# FIXME: the code here is outdated, and no longer working

import tlslite

from electrum.transaction import Transaction
from electrum import paymentrequest
from electrum import paymentrequest_pb2 as pb2
from electrum.bitcoin import address_to_script

chain_file = 'mychain.pem'
cert_file = 'mycert.pem'
amount = 1000000
address = "18U5kpCAU4s8weFF8Ps5n8HAfpdUjDVF64"
memo = "blah"
out_file = "payreq"


with open(chain_file, 'r') as f:
    chain = tlslite.X509CertChain()
    chain.parsePemList(f.read())

certificates = pb2.X509Certificates()
certificates.certificate.extend(map(lambda x: str(x.bytes), chain.x509List))

with open(cert_file, 'r') as f:
    rsakey = tlslite.utils.python_rsakey.Python_RSAKey.parsePEM(f.read())

script = address_to_script(address)

pr_string = paymentrequest.make_payment_request(amount, script, memo, rsakey)

with open(out_file,'wb') as f:
    f.write(pr_string)

print("Payment request was written to file '%s'"%out_file)
