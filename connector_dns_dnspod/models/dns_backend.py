# -*- coding: utf-8 -*-
# Copyright 2016 Elico Corp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import httplib
import json
import logging
import urllib
from openerp import _
from openerp import fields
from openerp import models, api
from openerp.addons.connector.queue.job import job

_logger = logging.getLogger(__name__)


class DNSPodBackend(models.Model):
    _inherit = 'dns.backend'

    version = fields.Selection(
        selection='_select_version',
        string='Service Provider',
        help='DNS service provider',
        required=True
    )

    @api.model
    def _select_version(self):
        res = []
        res.append(('dnspod', 'dnspod'))
        return res

    @api.multi
    def params(self):
        return {'format': 'json', 'login_email': self.login,
                'login_password': self.password}

    def request(self, action, params, method='POST'):
        """send request to 'dnsapi.cn'"""
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/json"
        }
        conn = httplib.HTTPSConnection("dnsapi.cn")
        conn.request(method, '/' + action, urllib.urlencode(params), headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        if response.status == 200:
            return data
        else:
            return None

    @api.multi
    def button_connect(self):
        for dns_backend in self:
            params = dns_backend.params()
            data = dns_backend.request('Domain.List', params)
            data = json.loads(data)
            if int(data['status']['code']) != -1:
                dns_backend.state = 'done'
            else:
                dns_backend.state = 'exception'

    @api.multi
    def button_set_draft(self):
        for dns_backend in self:
            dns_backend.state = 'draft'
