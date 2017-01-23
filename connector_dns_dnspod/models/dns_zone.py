# -*- coding: utf-8 -*-
# Copyright 2015 Elico Corp
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


class DNSPodZone(models.Model):
    _inherit = 'dns.zone'

    dns_id_external = fields.Char(
        compute="_get_dns_id_external",
        inverse="_set_dns_id_external",
        string='External ID',
        help='ID of the record in external system.',
    )

    @api.multi
    def _get_dns_id_external(self):
        dns_zone_bind_model = self.env['dns.zone.bind']
        for dns_zone in self:
            dns_zone_bind_ids = dns_zone_bind_model.search(
                [('odoo_id', '=', dns_zone.id)])
            if dns_zone_bind_ids:
                for dns_zone_bind_id in dns_zone_bind_ids:
                    return dns_zone_bind_id.dns_id_external

    @api.multi
    def _set_dns_id_external(self):
        dns_zone_bind_model = self.env['dns.zone.bind']
        for dns_zone in self:
            dns_zone_bind_id = dns_zone_bind_model.browse(
                [('odoo_id', '=', dns_zone.id)])
            if dns_zone_bind_id:
                return dns_zone_bind_id.write(
                    {'dns_id_external', dns_id_external})

    @api.multi
    def button_get_sub_domains(self):
        for dns_zone in self:
            # Create a job which import all the bindings of a record.
            session = ConnectorSession(
                dns_zone._cr,
                dns_zone._uid,
                context=dns_zone._context
            )
            if session.context.get('connector_no_export'):
                return
            data = {}
            data['format'] = 'json'
            data['login_email'] = dns_zone.dns_bind_ids[0].dns_backend_id.login
            data['login_password'] = dns_zone.dns_bind_ids[0].dns_backend_id.password
            data['domain_id'] = dns_zone.dns_bind_ids[0].dns_id_external
            import_record.delay(session, dns_zone.id, data)


@job
def import_record(session, dns_zone_id, data):
    dns_zone_bind_model = session.env['dns.zone.bind']
    dns_zone_model = session.env['dns.zone']
    dns_zone = dns_zone_model.browse(dns_zone_id)
    dns_record_bind_model = session.env['dns.record.bind']
    dns_record_model = session.env['dns.record']
    if not dns_zone:
        return _(u'Nothing to do because the record has been deleted.')

    try:
        dns_backend_id = dns_zone.dns_bind_ids[0].dns_backend_id
        result = dns_zone.dns_bind_ids[0].dns_backend_id.request(
            'Record.List',
            data,
            method='POST'
        )

        result_json = json.loads(result)
        if result_json['status']['code'] == '1':
            record_list_str = ''
            for record in result_json['records']:
                dns_record_bind_ids = dns_zone_bind_model.search(
                    [('dns_id_external', '=', record['id'])]
                )
                if dns_record_bind_ids:
                    dns_record_bind_id = dns_record_bind_ids[0]
                    dns_record_bind_id.write({
                        'dns_id_external': record['id']
                    })
                    dns_record_id = dns_record_bind_id.odoo_id
                    dns_record_id \
                        .with_context(connector_no_export=True) \
                        .write({
                            'zone_id': dns_zone_id,
                            'type': record['type'],
                            'line': record['line'],
                            'value': record['value'],
                            'mx_priority': record['mx'],
                            'ttl': record['ttl'],
                        })
                    record_list_str = '%s, %s.%s:%s' % (
                        record_list_str,
                        record['name'],
                        dns_zone.name,
                        record['value'])
                else:
                    dns_record_model \
                        .with_context(connector_no_export=True) \
                        .create({
                        'name': record['name'],
                        'zone_id': dns_zone_id,
                        'type': record['type'],
                        'line': record['line'],
                        'value': record['value'],
                        'mx_priority': record['mx'],
                        'ttl': record['ttl'],
                    })
                    dns_record_bind_id = dns_record_bind_model \
                        .create({
                            'dns_backend_id': dns_backend_id.id,
                            'dns_id_external': record['id'],
                            'odoo_id': dns_record_model.id
                        })

                    record_list_str = '%s, %s.%s:%s' % (
                        record_list_str,
                        dns_record_bind_id.odoo_id.name,
                        dns_zone.name,
                        dns_record_bind_id.odoo_id.value)
            return 'Import record success %s' % record_list_str
        else:
            return _('Import record error code: %s' %
                     result_json['status']['code'])
    except:
        raise
