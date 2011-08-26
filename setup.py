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

from distutils.core import setup
import os.path

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='openerp-client-lib',
      version='1.0.0',
      description='OpenERP Client Library allows to easily interact with OpenERP in Python.',
      author='Nicolas Vanhoren',
      author_email='niv@openerp.com',
      url='',
      packages=["openerplib"],
      long_description=read("README"),
      keywords="openerp library com communication rpc xml-rpc net-rpc xmlrpc python client lib web service",
     )
