# -*- coding: utf-8 -*-
# Copyright 2015 Elico Corp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import openerp.addons.connector.backend as backend
from openerp.addons.connector_dns.backend import dns

dnspod = backend.Backend(parent=dns, version='dnspod')
