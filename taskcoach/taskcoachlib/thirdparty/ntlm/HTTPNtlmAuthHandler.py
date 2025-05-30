"""
urllib auth handler for ntlm
"""

# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>
# or <http://www.gnu.org/licenses/lgpl.txt>.

import socket
import re

from six.moves import urllib
from six.moves.http_client import HTTPConnection, HTTPSConnection

from . import ntlm


class AbstractNtlmAuthHandler:
    """
    urllib auth handler for NTLM baseclass.
    """

    auth_header = ""

    def __init__(self, password_mgr=None, debuglevel=0, header="NTLM"):
        if password_mgr is None:
            password_mgr = urllib.request.HTTPPasswordMgr()
        self.header = header
        self.passwd = password_mgr
        self.add_password = self.passwd.add_password
        self._debuglevel = debuglevel

    def set_http_debuglevel(self, level):
        """
        Used to adjust debug.
        """
        self._debuglevel = level

    def http_error_authentication_required(self, auth_header_field, req, fp, headers):
        """
        Called if authorization needed.
        """
        auth_header_value = headers.get(auth_header_field, None)
        if auth_header_field:
            if auth_header_value is not None and (
                "ntlm" in auth_header_value.lower()
                or "negotiate" in auth_header_value.lower()
            ):
                fp.Close()
                return self.retry_using_http_NTLM_auth(
                    req, auth_header_field, None, headers
                )

    def retry_using_http_NTLM_auth(self, req, auth_header_field, realm, headers):
        """
        Retry the original request with the NTLM auth headers
        """
        user, pw = self.passwd.find_user_password(realm, req.get_full_url())
        if pw is None:
            return None
        user_parts = user.split("\\", 1)
        if len(user_parts) == 1:
            UserName = user_parts[0]
            DomainName = ""
            type1_flags = ntlm.NTLM_TYPE1_FLAGS & ~ntlm.NTLM_NegotiateOemDomainSupplied
        else:
            DomainName = user_parts[0].upper()
            UserName = user_parts[1]
            type1_flags = ntlm.NTLM_TYPE1_FLAGS
            # ntlm secures a socket, so we must use the same socket for the complete handshake
        headers = dict(req.headers)
        headers.update(req.unredirected_hdrs)
        auth = "%s %s" % (
            self.header,
            ntlm.create_NTLM_NEGOTIATE_MESSAGE(user, type1_flags).decode("ascii"),
        )
        auth_header_val = req.headers.get(self.auth_header, None)
        if auth_header_val == auth:
            return None
        headers[self.auth_header] = auth

        host = req.host

        if not host:
            # raise urllib.request.URLError("no host given")
            raise urllib.error.URLError("no host given")

        h = None

        if req.get_full_url().startswith("https://"):
            h = HTTPSConnection(host)  # will parse host:port
        else:
            h = HTTPConnection(host)  # will parse host:port

        h.set_debuglevel(self._debuglevel)

        # we must keep the connection because NTLM authenticates the connection, not single requests
        headers["Connection"] = "Keep-Alive"
        headers = dict((name.title(), val) for name, val in headers.items())

        # For some reason, six doesn't do this translation correctly
        # TODO rsanders low - find bug in six & fix it
        try:
            selector = req.selector
        except AttributeError:
            selector = req.get_selector()

        h.request(req.get_method(), selector, req.data, headers)

        r = h.getresponse()

        r.begin()

        r._safe_read(int(r.getheader("content-length")))
        if r.getheader("set-cookie"):
            # this is important for some web applications that store
            # authentication-related info in cookies (it took a long time to
            # figure out)
            headers["Cookie"] = r.getheader("set-cookie")
        r.fp = None  # remove the reference to the socket, so that it can not be
        # closed by the response object (we want to keep the socket open)
        auth_header_value = r.getheader(auth_header_field, None)

        # some Exchange servers send two WWW-Authenticate headers, one with the NTLM challenge
        # and another with the 'Negotiate' keyword - make sure we operate on the right one
        m = re.match("(NTLM [A-Za-z0-9+\\-/=]+)", auth_header_value)
        if m:
            (auth_header_value,) = m.groups()

        if auth_header_value.startswith("NTLM"):
            msg2 = auth_header_value[5:]
        elif auth_header_value.startswith("Negotiate"):
            msg2 = auth_header_value[10:]

        (ServerChallenge, NegotiateFlags) = ntlm.parse_NTLM_CHALLENGE_MESSAGE(msg2)
        auth = "%s %s" % (
            self.header,
            ntlm.create_NTLM_AUTHENTICATE_MESSAGE(
                ServerChallenge, UserName, DomainName, pw, NegotiateFlags
            ).decode("ascii"),
        )
        headers[self.auth_header] = auth
        headers["Connection"] = "Close"
        headers = dict((name.title(), val) for name, val in headers.items())
        try:
            h.request(req.get_method(), selector, req.data, headers)
            # none of the configured handlers are triggered, for example
            # redirect-responses are not handled!
            response = h.getresponse()

            def notimplemented():
                raise NotImplementedError

            response.readline = notimplemented
            infourl = urllib.response.addinfourl(
                response, response.msg, req.get_full_url()
            )
            infourl.code = response.status
            infourl.msg = response.reason
            return infourl
        except socket.error as err:
            raise urllib.error.URLError(err)


class HTTPNtlmAuthHandler(AbstractNtlmAuthHandler, urllib.request.BaseHandler):
    """
    Standard HTTP NTLM Auth Handler
    """

    auth_header = "Authorization"

    def http_error_401(
        self, req, fp, code, msg, headers
    ):  # pylint: disable=unused-argument
        """
        Handler for 401 auth required
        """
        return self.http_error_authentication_required(
            "www-authenticate", req, fp, headers
        )


class ProxyNtlmAuthHandler(AbstractNtlmAuthHandler, urllib.request.BaseHandler):
    """
    CAUTION: this class has NOT been tested at all!!!
    use at your own risk
    """

    auth_header = "Proxy-authorization"

    def http_error_407(
        self, req, fp, code, msg, headers
    ):  # pylint: disable=unused-argument
        """
        Handler for 407 proxy auth required
        """
        return self.http_error_authentication_required(
            "proxy-authenticate", req, fp, headers
        )
