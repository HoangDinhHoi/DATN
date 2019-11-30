# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_close(self):
        pos_orders = self.env['pos.order'].search([('session_id', '=', self.id), ('x_revenue', '!=', 0)])
        for line in pos_orders:
            revenue_allocation_id = self.env['pos.revenue.allocation'].search([('order_id', '=', line.id)])
            if not revenue_allocation_id:
                raise except_orm("Thông báo!", ('Đơn hàng "%s" chưa được phân bổ. Vui lòng phân bổ trước khi đóng phiên' % line.name))
            if revenue_allocation_id.state not in ('confirmed'):
                raise except_orm('Cảnh báo!', (
                        'Đơn sử phân bổ doanh thu của đơn hàng "%s" chưa được hoàn thiện. Vui lòng hoàn thành trước khi đóng phiên' % line.name))
        return super(PosSession, self).action_pos_session_close()