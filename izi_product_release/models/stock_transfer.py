# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class StockTransferInherit(models.Model):
    _inherit = 'stock.transfer'
    
    @api.multi
    def action_receive(self):
        res = super(StockTransferInherit, self).action_receive()
        product_release_id = self.env['product.release'].search([('name', '=', self.origin)])
        if len(product_release_id):
            product_release_id.write({'state': 'done'})
        return res