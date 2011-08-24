# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 OpenERP s.a. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""
OpenObject Client Library
"""

import xmlrpclib
import logging 
import socket

try:
    import cPickle as pickle
    pickle.__name__
except:
    import pickle

try:
    import cStringIO as StringIO
    StringIO.__name__
except:
    import StringIO

_logger = logging.getLogger(__name__)

def _getChildLogger(logger, subname):
    return logging.getLogger(logger.name + "." + subname)

class Connector(object):
    """
    Connector class
    """

    __logger = _getChildLogger(_logger, 'connector')

    def __init__(self, hostname, port):
        """
        :param hostname: Host name of the server
        :param port: Port for the connection to the server
        """
        self.hostname = hostname
        self.port = port

class XmlRPCConnector(Connector):
    """
    This class supports the XmlRPC protocol
    """
    PROTOCOL = 'xmlrpc'
    
    __logger = _getChildLogger(_logger, 'connector.xmlrpc')

    def __init__(self, hostname, port=8069):
        Connector.__init__(self, hostname, port)
        self.url = 'http://%s:%d/xmlrpc' % (self.hostname, self.port)

    def send(self, service_name, method, *args):
        url = '%s/%s' % (self.url, service_name)
        service = xmlrpclib.ServerProxy(url)
        return getattr(service, method)(*args)

class NetRPC_Exception(Exception):
    def __init__(self, faultCode, faultString):
        self.faultCode = faultCode
        self.faultString = faultString
        self.args = (faultCode, faultString)

class NetRPC:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.sock.settimeout(120)
    def connect(self, host, port=False):
        if not port:
            buf = host.split('//')[1]
            host, port = buf.split(':')
        self.sock.connect((host, int(port)))

    def disconnect(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def mysend(self, msg, exception=False, traceback=None):
        msg = pickle.dumps([msg,traceback])
        size = len(msg)
        self.sock.send('%8d' % size)
        self.sock.send(exception and "1" or "0")
        totalsent = 0
        while totalsent < size:
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError, "socket connection broken"
            totalsent = totalsent + sent

    def myreceive(self):
        buf=''
        while len(buf) < 8:
            chunk = self.sock.recv(8 - len(buf))
            if chunk == '':
                raise RuntimeError, "socket connection broken"
            buf += chunk
        size = int(buf)
        buf = self.sock.recv(1)
        if buf != "0":
            exception = buf
        else:
            exception = False
        msg = ''
        while len(msg) < size:
            chunk = self.sock.recv(size-len(msg))
            if chunk == '':
                raise RuntimeError, "socket connection broken"
            msg = msg + chunk
        msgio = StringIO.StringIO(msg)
        unpickler = pickle.Unpickler(msgio)
        unpickler.find_global = None
        res = unpickler.load()

        if isinstance(res[0],Exception):
            if exception:
                raise NetRPC_Exception(str(res[0]), str(res[1]))
            raise res[0]
        else:
            return res[0]

class NetRPCConnector(Connector):
    PROTOCOL = 'netrpc'
    
    __logger = _getChildLogger(_logger, 'connector.netrpc')

    def __init__(self, hostname, port=8070):
        Connector.__init__(self, hostname, port)

    def send(self, service_name, method, *args):
        socket = NetRPC()
        socket.connect(self.hostname, self.port)
        socket.mysend((service_name, method, )+args)
        result = socket.myreceive()
        socket.disconnect()
        return result
    
class Service:
    
    def __init__(self, connector, service_name):
        self.connector = connector
        self.service_name = service_name
        self.__logger = _getChildLogger(_getChildLogger(_logger, 'service'),service_name)
        
    def __getattr__(self, method):
        """
        :param method: The method for the linked object (search, read, write, unlink, create, ...)
        """
        self.__logger.debug('method: %r', method)
        def proxy(*args):
            """
            :param args: A list of values for the method
            """
            self.__logger.debug('args: %r', args)
            result = self.connector.send(self.service_name, method, *args)
            self.__logger.debug('result: %r' % result)
            return result
        return proxy

class Connection(object):
    """
    TODO: Document this class
    """
    __logger = _getChildLogger(_logger, 'connection')

    def __init__(self, connector,
                 database=None,
                 login=None,
                 password=None,
                 user_id=None):
        """
        :param connector:
        :param database:
        :param login:
        :param password:
        """
        self.connector = connector

        self.set_login_info(database, login, password, user_id)

    def set_login_info(self, database, login, password, user_id=None):
        self.database, self.login, self.password = database, login, password

        self.user_id = user_id
        
    def check_login(self, force=True):
        if self.user_id and not force:
            return
        
        self.user_id = self.get_service("common").login(self.database, self.login, self.password)
        if not self.user_id:
            raise Exception("Authentification failure")
        self.__logger.debug("Authentified with user id %s" % self.user_id)
    
    def get_object(self, model):
        return Object(self, model)

    def get_service(self, service_name):
        return Service(self.connector, service_name)

class Object(object):
    """
    TODO: Document this class
    """

    def __init__(self, connection, model):
        """
        :param connection:
        :param model:
        """
        self.connection = connection
        self.model = model
        self.__logger = _getChildLogger(_getChildLogger(_logger, 'object'),model)

    def __getattr__(self, method):
        """
        :param method: The method for the linked object (search, read, write, unlink, create, ...)
        """
        #self.__logger.debug('method: %r', method)
        def proxy(*args):
            """
            :param args: A list of values for the method
            """
            self.connection.check_login(False)
            self.__logger.debug(args)
            result = self.connection.get_service('object').execute(
                                                    self.connection.database,
                                                    self.connection.user_id,
                                                    self.connection.password,
                                                    self.model,
                                                    method,
                                                    *args)
            if method == "read":
                if isinstance(result, list) and len(result) > 0 and "id" in result[0]:
                    index = {}
                    for i in xrange(len(result)):
                        index[result[i]["id"]] = result[i]
                    result = [index[x] for x in args[0]]
            self.__logger.debug('result: %r' % result)
            return result
        return proxy

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, context=None):
        record_ids = self.search(domain or [], offset, limit or False, order or False, context or {})
        records = self.read(record_ids, fields or [], context or {})
        return records

def get_connection(hostname, protocol="xmlrpc", port='auto', database=None,
                 login=None, password=None, user_id=None):
    if port == 'auto':
        port = 8069 if protocol=="xmlrpc" else 8070
    if protocol == "xmlrpc":
        return Connection(XmlRPCConnector(hostname, port), database, login, password, user_id)
    elif protocol == "netrpc":
        return Connection(NetRPCConnector(hostname, port), database, login, password, user_id)
    else:
        raise ValueError("You must choose xmlrpc or netrpc")

