# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import sys
import math
import time
import gettext

# ---------------
# Twisted imports
# ---------------

from zope.interface       import implementer
from twisted.web.iweb     import IPolicyForHTTPS # agnadido por mi
from twisted.web.client   import BrowserLikePolicyForHTTPS
from twisted.internet     import ssl
from twisted.internet.ssl import CertificateOptions

# -------------------
# Third party imports
# -------------------

#--------------
# local imports
# -------------


# -------------------------
# Utility class definitions
# -------------------------

@implementer(IPolicyForHTTPS)
class WhitelistContextFactory(object):
    def __init__(self, good_domains=None):
        """
        :param good_domains: List of domains. The URLs must be in bytes
        """
        if not good_domains:
            self.good_domains = []
        else:
            self.good_domains = good_domains

        # by default, handle requests like a browser would
        self.default_policy = BrowserLikePolicyForHTTPS()

    def creatorForNetloc(self, hostname, port):
        # check if the hostname is in the the whitelist, otherwise return the default policy
        if hostname in self.good_domains:
            return ssl.CertificateOptions(verify=False)
        return self.default_policy.creatorForNetloc(hostname, port)