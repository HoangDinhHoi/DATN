# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging

logger = logging.getLogger(__name__)

TYPE_SELECTOR = [('retail', 'Retail customer'), ('wholesale', 'Wholesale customer')]
STATE_SELECTOR = [('draft', 'Quotation'), ('sent', 'Quotation Sent'), ('sale', 'Sales Order'),
                  ('moved_to_pos', 'Moved to pos'), ('done', 'Done'), ('cancel', 'Cancelled')]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    type = fields.Selection(TYPE_SELECTOR, string='Type', default='wholesale')
    pos_order_ids = fields.One2many('pos.order', 'sale_order_id', string='Pos order')
    state = fields.Selection(STATE_SELECTOR, string='Status', readonly=True, copy=False, index=True,
                             track_visibility='onchange', track_sequence=3, default='draft')

    @api.model
    def create(self, vals):
        type = vals.get('type', '') or self._context.get('default_type', '')
        if vals.get('name', 'New') == 'New' and type == 'retail':
            vals['name'] = self.env['ir.sequence'].next_by_code('so_retail_seq')

        return super(SaleOrder, self).create(vals)

    @api.multi
    def action_move_to_pos(self):
        return self.env['sale.order.make.pos.order'].with_context(sale_order_id=self.id).get_dialog()
