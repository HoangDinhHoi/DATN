# -*- coding: utf-8 -*-
__author__ = "HoiHD"

from odoo import models, fields, api, exceptions
import odoo.tools.config as config


class ByPayment(models.TransientModel):
    _name = 'rpt.by.payment'

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    branch_id = fields.Many2one('res.branch', string="Branch",
                                domain=lambda self: [('id', 'in', self.env.user.branch_ids.ids)])
    is_export_excel = fields.Boolean(default=False, string='Export to Excel')

    @api.multi
    def action_report(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("You must config birt_url in file config")
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        report_name = "rpt_pos_by_payment.rptdesign"
        param_str = {
            '&date_from': date_from,
            '&date_to': date_to,
            '&branch_id': str(self.branch_id.id) if self.branch_id else '0',
        }
        birt_link = birt_url + report_name
        if self.is_export_excel is True:
            birt_link += '&__format=xlsx'
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo ngăn kéo',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }

