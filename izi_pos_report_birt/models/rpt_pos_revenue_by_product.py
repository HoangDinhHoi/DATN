# -*- coding: utf-8 -*-
__author__ = "HoiHD"

from odoo import fields, models, api, exceptions
import odoo.tools.config as config


class ReportPosRevenueByProduct(models.TransientModel):
    _name = 'rpt.pos.revenue.by.product'
    _description = 'Báo cáo doanh thu theo sản phẩm'

    branch_id = fields.Many2one('res.branch', string='Branch',
                                  domain=lambda self: [('id', 'in', self.env.user.branch_ids.ids)],
                                  help='Để trống nếu như bạn muốn xem toàn bộ chi nhánh.')
    from_date = fields.Date(string='From Date', help='Chọn ngày bắt đầu')
    to_date = fields.Date(string='To Date', help='Chọn ngày kết thúc')
    export_excel = fields.Boolean(default=False, string='Export to Excel',
                                  help='Chọn nếu như bạn muốn xuất sang định dạng excel.')

    @api.multi
    def export_report(self):
        birt_url = config['birt_url'] or '0'
        if not birt_url:
            raise exceptions.ValidationError('Bạn phải cấu hình thông số birt_url trong file config.')

        param_string = {
            '&branch_id': str(self.branch_id.id if self.branch_id else 0),
            '&from_date': self.from_date.strftime('%d/%m/%Y'),
            '&to_date': self.to_date.strftime('%d/%m/%Y')
        }
        report_name = 'rpt_pos_revenue by product.rptdesign'
        birt_link = birt_url + report_name
        if self.export_excel is True:
            birt_link += '&__format=xlsx'
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo doanh thu theo sản phẩm',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_string,
            }
        }
