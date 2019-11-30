# -*- coding: utf-8 -*-
__author__ = 'HoiHD'

import odoo.tools.config as config
from odoo import models, fields, api, exceptions


class RevenueAllocationEmployee(models.TransientModel):
    _name = 'rpt.revenue.allocation.employee'
    _description = '- Báo cáo phân bổ doanh thu cho nhân viên ' \
                   '- Báo cáo phân bổ chi tiết doanh thu cho nhân viên'

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    branch_id = fields.Many2one('res.branch', string='Branch',
                                domain=lambda self: [('id', 'in', self.env.user.branch_ids.ids)])
    branch_detail_id = fields.Many2one('res.branch', string='Branch',
                                       domain=lambda self: [('id', 'in', self.env.user.branch_ids.ids)])
    is_export_excel = fields.Boolean(default=False, string='Export to Excel')

    @api.multi
    def action_report(self):
        """
            Báo cáo phân bổ doanh thu cho nhân viên
        :return:
        """
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("Chưa cấu hình birl_url!")
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        report_name = "rpt_pos_allocation_employee.rptdesign"
        param_str = {
            '&date_from': date_from,
            '&date_to': date_to,
            '&branch_id': str(self.branch_id.id) if self.branch_id else '0',
        }
        birl_link = birt_url + report_name
        if self.is_export_excel is True:
            birl_link += '&__format=xlsx'
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo phân bổ doanh thu nhân viên',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birl_link,
                'payload_data': param_str,
            }
        }

    @api.multi
    def action_report_detail_allocation(self):
        """
            - Báo cáo phân bổ chi tiết doanh thu cho nhân viên
        :return:
        """
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("Chưa cấu hình birl_url!")
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        report_name = "rpt_pos_allocation_employee_detail.rptdesign"
        param_str = {
            '&date_from': date_from,
            '&date_to': date_to,
            '&branch_id': str(self.branch_detail_id.id),
        }
        birl_link = birt_url + report_name
        if self.is_export_excel is True:
            birl_link += '&__format=xlsx'
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo phân bổ chi tiết doanh thu nhân viên',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birl_link,
                'payload_data': param_str,
            }
        }
