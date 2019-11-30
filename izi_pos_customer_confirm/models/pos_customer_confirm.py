# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosCustomerConfirm(models.Model):
    _name = 'pos.customer.confirm'

    signature = fields.Binary('Signature')
    partner_id = fields.Many2one('res.partner', "Partner")
    order_ids = fields.One2many('pos.order', 'x_custmer_confirm_id', string="Order")
    order_line_ids = fields.One2many('pos.order.line','x_custmer_confirm_id', string="Order Line")
    use_service_ids = fields.One2many('pos.use.service', 'custmer_confirm_id', string="Use Service")
    use_service_line_ids = fields.One2many('pos.use.service.line','custmer_confirm_id', string="Use Service Line")
    state = fields.Selection([('draft', "Draft"), ('done', "Done")], default='draft')
    date = fields.Date("Date")

    @api.multi
    def action_confirm(self):
        for line in self.order_ids:
            line.x_signature = self.signature
            line.state = 'paid'
        for line in self.use_service_ids:
            if line.pos_order_id:
                line.pos_order_id.x_signature = self.signature
            line.signature = self.signature
            line.state = 'done'
        return
        # if self.order_id:
        #     self.order_id.x_signature = self.signature
        #     self.order_id.state = 'paid'
        # if self.pos_use_service_id:
        #     # if self.pos_use_service_id.pos_order_id:
        #     #     self.pos_use_service_id.pos_order_id.x_signature = self.signature
        #     # self.pos_use_service_id.signature = self.signature
        #     for line in self.use_service_line_ids:
        #         for x in self.pos_use_service_id.use_service_ids:
        #             if line.id == x.id:
        #                 x.customer_rate = line.customer_rate
        #     self.pos_use_service_id.state = 'done'
        # return

