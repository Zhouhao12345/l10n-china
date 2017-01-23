# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.connector.unit.mapper import mapping, ExportMapper
from ..unit.backend_adapter import DNSPodAdapter
from ..unit.export_synchronizer import DNSExporter
from ..unit.delete_synchronizer import DNSDeleter
from ..backend import dnspod


@dnspod
class DNSZoneExport(DNSExporter):
    _model_name = ['dns.zone.bind']


@dnspod
class DNSZoneAdapter(DNSPodAdapter):
    _model_name = 'dns.zone.bind'
    _dns_model = 'Zone'


@dnspod
class DNSZoneExportMapper(ExportMapper):
    _model_name = 'dns.zone.bind'
    direct = [('name', 'zone')]

    @mapping
    def default(self, record):
        return {
            'format': 'json',
            'login_email': record.backend_id.login,
            'login_password': record.backend_id.password
        }

@dnspod
class DNSRecordDeleter(DNSDeleter):
    _model_name = ['dns.record.bind']


@dnspod
class DNSRecordExport(DNSExporter):
    _model_name = ['dns.record.bind']


@dnspod
class DNSRecordAdapter(DNSPodAdapter):
    _model_name = 'dns.record.bind'
    _dns_model = 'Record'


@dnspod
class DNSRecordExportMapper(ExportMapper):
    _model_name = 'dns.record.bind'
    direct = [('name', 'record')]

    @mapping
    def default(self, record):
        result = {
            'format': 'json',
            'login_email': record.zone_id.backend_id.login,
            'login_password': record.zone_id.backend_id.password,
            'record_id': record.record_id,
            'domain_id': record.zone_id.dns_id_external,
            'sub_zone': record.name,
            'record_type': record.type,
            'record_line': record.line.encode('utf-8'),
            'value': record.value,
            'mx': record.mx_priority,
            'ttl': record.ttl,
        }
        return result
