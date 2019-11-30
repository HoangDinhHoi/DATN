# -*- coding: utf-8 -*-
__author__ = "HoiHD"

import odoo.tools.config as config
from odoo import models, fields, api, _, exceptions


class ReportListCardAccordingToBranch(models.TransientModel):
    _name = 'rpt.list.card.branch'
    _description = 'Báo cáo danh sách thẻ theo chi nhánh'

    branch_id = fields.Many2one('res.branch',
                                string=_('Branch'),
                                domain=lambda self: [('id', 'in', self.env.user.branch_ids.ids)])
    type_card = fields.Selection([
        ('service_card', _('Service Card')),
    ], string=_('Card Type'), default="service_card")
    state = fields.Selection([
        ('new', _('New')),
        ('activated', _('Activated')),
        ('using', _('Using')),
        ('used', _('Used')),
        ('destroy', _('Destroy'))
    ], default='using', string=_('Status'),
        help='Lựa chọn trạng thái của thẻ, nếu muốn lấy ra tất cả thì hãy để trống.')
    partner_id = fields.Many2one('res.partner', string=_('Purchaser'),
                                 help='Lựa chọn khách hàng mua thẻ, nếu muốn lấy ra tất cả thì hãy để trống.')
    customer_id = fields.Many2one('res.partner', string=_('User'),
                                  help='Lựa chọn người sử dụng thẻ, nếu muốn lấy ra tất cả thì hãy để trống.')
    is_print_excel = fields.Boolean(default=False, string='Print Excel')

    @api.multi
    def action_print(self):
        birt_url = config['birt_url'] or '0'
        if not birt_url:
            raise exceptions.ValidationError('Bạn phải cấu hình thông số birt_url trong file config.')
        report_name = ''
        params_str = {
            '&branch_id': str(self.branch_id.id),
            '&state': self.state if self.state else '0',
            '&partner_id': str(self.partner_id.id) if self.partner_id else '0'
        }
        if self.type_card == 'voucher':
            params_str.update({'&customer_id': str(self.customer_id.id) if self.customer_id else '0'})
            report_name = 'rpt_pos_list_card_branch_by_voucher.rptdesign'

        else:
            self.customer_id = False
            params_str.update({'&card_type': self.type_card})
            report_name = 'rpt_pos_list_card_branch_by_service_card.rptdesign'
        birt_link = birt_url + report_name
        if self.is_print_excel is True:
            birt_link += '&__format=xlsx'
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo danh sách thẻ theo chi nhánh',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': params_str,
            }
        }
