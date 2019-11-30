# -*- coding: utf-8 -*-
# edit by: HoiHD: chuyen view report birt sang view hien tai.

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import except_orm
import odoo.tools.config as config


class RptStockTransferIntype(models.TransientModel):
    _name = 'rpt.stock.transfer.intype'

    @api.multi
    def _default_branch_id(self):
        branch_id = self.env['res.users'].browse(self._uid).branch_id.id
        return branch_id

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    type = fields.Selection([('in', 'In'), ('out', 'Out'), ('int', 'Internal')], string='Type', default='in')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('res.branch', default=_default_branch_id)
    location_id = fields.Many2one('stock.location', string='Location')
    location_ids = fields.Many2many('stock.location', string='Source Locations')
    location_dest_ids = fields.Many2one('stock.location', string='Destination Locations')

    @api.multi
    def action_report(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("You must config birt_url in file config")
        report_name = ''
        location_id = str(self.location_id.id) if self.location_id else '0'
        location_ids = '0'
        if self.location_ids:
            for location in self.location_ids:
                location_ids += ',' + str(location.id)
        location_dest_ids = '0'
        if self.location_dest_ids:
            for location in self.location_dest_ids:
                location_ids += ',' + str(location.id)
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        report_name_cus = "rpt_stock_cus.rptdesign"
        report_name_sup = "rpt_stock_sup.rptdesign"
        report_name_int = "rpt_stock_int.rptdesign"
        if self.type == 'in':
            report_name = report_name_sup
            param_str = {
                '&from_date': date_from,
                '&to_date': date_to,
                '&location_id': location_id,
            }
        elif self.type == 'out':
            report_name = report_name_cus
            param_str = {
                '&from_date': date_from,
                '&to_date': date_to,
                '&location_id': location_id,
            }
        else:
            report_name = report_name_int
            param_str = {
                '&from_date': date_from,
                '&to_date': date_to,
                '&location_id': location_ids,
                '&location_dest_id': location_dest_ids,
            }
        return {
            "type": "ir.actions.client",
            'name': 'POS Document',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_url + report_name,
                'payload_data': param_str,
            }
        }

    @api.multi
    def action_report_excel(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("You must config birt_url in file config")
        report_name = ''
        location_id = str(self.location_id.id) if self.location_id else '0'
        location_ids = '0'
        if self.location_ids:
            for location in self.location_ids:
                location_ids += ',' + str(location.id)
        location_dest_ids = '0'
        if self.location_dest_ids:
            for location in self.location_dest_ids:
                location_ids += ',' + str(location.id)
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        report_name_cus = "rpt_stock_cus.rptdesign"
        report_name_sup = "rpt_stock_sup.rptdesign"
        report_name_int = "rpt_stock_int.rptdesign"
        if self.type == 'in':
            report_name = report_name_sup
            param_str = {
                '&from_date': date_from,
                '&to_date': date_to,
                '&location_id': location_id,
            }
        elif self.type == 'out':
            report_name = report_name_cus
            param_str = {
                '&from_date': date_from,
                '&to_date': date_to,
                '&location_id': location_id,
            }
        else:
            report_name = report_name_int
            param_str = {
                '&from_date': date_from,
                '&to_date': date_to,
                '&location_id': location_ids,
                '&location_dest_id': location_dest_ids,
            }
        return {
            "type": "ir.actions.client",
            'name': 'POS Document',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_url + report_name + '&__format=xlsx',
                'payload_data': param_str,
            }
        }