# -*- coding: utf-8 -*-
# Created by Hoanglv on 9/4/2019

from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    sale_order_id = fields.Many2one('sale.order', string='Sale order')

    @api.multi
    def action_detail(self):
        view_id = self.env.ref('point_of_sale.view_pos_pos_form').id
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'res_id': self.id,
            'context': dict(self._context),
        }
