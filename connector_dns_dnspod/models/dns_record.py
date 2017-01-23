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
from openerp.addons.connector.session import ConnectorSession

_logger = logging.getLogger(__name__)


class DNSPodRecord(models.Model):
    _inherit = 'dns.record'

    def _type_select_version(self):
        res = [('A', 'A'), ('CNAME', 'CNAME'), ('MX', 'MX'),
               ('TXT', 'TXT'), ('NS', 'NS'), ('AAAA', 'AAAA'),
               ('SRV', 'SRV'), ('Visibile URL', '显性URL'),
               ('Invisible URL', '隐现URL')]
        return res

    def _line_select_version(self):
        res = [(u'\u9ed8\u8ba4', '默认'), ('B', '电信'), ('C', '联通'),
               ('D', '教育网'), ('E', '百度'), ('F', '搜索引擎')]
        return res

    @api.multi
    def unlink(self):
        for dns_record in self:
            dns_zone_bind_model = session.env['dns.zone.bind']
            dns_record_bind_ids = dns_zone_bind_model.search(
                [('odoo_id', '=', dns_record.id)])
            if dns_record_bind_ids:
                for dns_record_bind_id in dns_record_bind_ids:
                    if dns_record_bind_id.dns_id_external == 0:
                        super(DNSPodRecord, dns_record).unlink()
                    else:
                        dns_record.delete_record(dns_record_bind_id.dns_id_external)

    @api.model
    def delete_record(self, dns_id_external):
        """ Create a job which delete all the bindings of a record. """
        session = ConnectorSession(self._cr, self._uid, context=self._context)
        data = {}
        data['format'] = 'json'
        data['login_email'] = self.dns_backend_id.login
        data['login_password'] = self.dns_backend_id.password
        data['domain_id'] = self.zone_id.dns_id_external
        data['dns_id_external'] = dns_id_external
        export_delete_record.delay(
            session,
            self._model._name,
            self.backend_id.id,
            self.id,
            data=data
        )
