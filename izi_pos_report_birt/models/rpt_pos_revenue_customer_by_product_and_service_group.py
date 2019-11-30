# -*- coding: utf-8 -*-
__author__ = "HoiHD"

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import odoo.tools.config as config


class ReportRevenueCustomerAccordingToProductAndServiceGroup(models.TransientModel):
    _name = 'rpt.revenue.customer.product.service.group'
    _description = 'Báo cáo doanh thu của khách hàng theo nhóm sản phẩm và dịch vụ'

    branch_id = fields.Many2one('res.branch', string='Branch',
                                domain=lambda self: [('id', 'in', self.env.user.branch_ids.ids)])
    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')
    is_export_excel = fields.Boolean(default=False, string='Export to Excel')

    @api.multi
    def action_report(self):
        """
            - Báo cáo doanh thu của khách hàng theo nhóm sản phẩm và dịch vụ
            - date: 11/06/2019 on 9:01 AM
        :return:
        """
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise ValidationError("Chưa cấu hình birt_url!")
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        report_name = "rpt_pos_revenue_customer_by_product_and_service_group.rptdesign"
        param_str = {
            '&date_from': date_from,
            '&date_to': date_to,
            '&branch_id': str(self.branch_id.id if self.branch_id else 0),
        }
        birt_link = birt_url + report_name
        if self.is_export_excel:
            birt_link += '&__format=xlsx'
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo doanh thu của khách hàng theo nhóm sản phẩm và dịch vụ',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }
