# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm

class PosOrder(models.Model):
    _inherit = 'pos.order'

    revenue_allocation_ids = fields.One2many('pos.revenue.allocation', 'order_id', "Revenue Allocation")

    @api.multi
    def action_revenue_allocation(self):
        allo = self.env['pos.revenue.allocation'].search([('order_id', '=', self.id)], limit=1)
        if allo.id != False:
            view = self.env.ref('izi_pos_revenue_allocation.izi_pos_revenue_allocation_form')
            return {
                'name': _('Phân bổ doanh thu'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.revenue.allocation',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'res_id': allo.id,
                'target': 'new',
                'context': self.env.context,
            }
        else:
            if self.amount_total == 0:
                raise except_orm('Cảnh báo!', (
                    "Số tiền KH thanh toán bằng 0. Không có gì để phân bổ"))
            if self.env.context is None:
                context = {}
            ctx = self.env.context.copy()
            ctx.update({'default_order_id': self.id
                        })
            view = self.env.ref('izi_pos_revenue_allocation.izi_pos_revenue_allocation_form')
            return {
                'name': _('Revenue Allocation?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.revenue.allocation',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,
            }