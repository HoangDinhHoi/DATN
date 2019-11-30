# -*- coding: utf-8 -*-
__author__ = "HoiHD"

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import except_orm
import odoo.tools.config as config


class RevenueShopDaily(models.TransientModel):
    _name = 'rpt.revenue.shop.daily'
    _description = 'Doanh thu chi nhánh theo ngày'

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    branch_id = fields.Many2one('res.branch', string="Branch",
                                 domain=lambda self: [('id', 'in', self.env.user.branch_ids.ids)])
    export_excel = fields.Boolean(string='Export to Excel', default=False)

    @api.multi
    def action_report(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("You must config birt_url in file config")
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        report_name = "rpt_pos_revenue_shop_daily.rptdesign"
        param_str = {
            '&date_from': date_from,
            '&date_to': date_to,
            '&branch_id': str(self.branch_id.id if self.branch_id else 0),
        }
        birt_link = birt_url + report_name
        if self.export_excel is True:
            birt_link += '&__format=xlsx'
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo doanh thu chi nhánh theo ngày',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }
