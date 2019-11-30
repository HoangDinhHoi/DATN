# -*- coding: utf-8 -*-
# edit by: HoiHD: chuyen view report birt sang view hien tai.

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import except_orm
import odoo.tools.config as config


class RptStockDelivery(models.TransientModel):
    _name = 'rpt.stock.delivery'

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    type = fields.Selection([('in', 'In'), ('out', 'Out')], string='Type', default='in')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    location_id = fields.Many2one('stock.location', 'Location')

    @api.multi
    def action_report(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("You must config birt_url in file config")
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        report_name = "rpt_stock_delivery.rptdesign"
        param_str = {
            '&date_from': date_from,
            '&date_to': date_to,
            '&type': self.type,
            '&location_id': str(self.location_id.id),
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
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        report_name = "rpt_stock_delivery.rptdesign"
        param_str = {
            '&date_from': date_from,
            '&date_to': date_to,
            '&type': self.type,
            '&location_id': str(self.location_id.id),
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