# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class ProductRecipeLine(models.Model):
    _name = 'product.recipe.line'

    sequence = fields.Integer('Sequence LT')
    name = fields.Char('Name LT')
    product_id = fields.Many2one('product.product', "Product")
    uom_id = fields.Many2one('uom.uom', "Uom")
    qty = fields.Float("Qty")
    product_recipe_id = fields.Many2one('product.template', "Product Recipe")

    @api.onchange('product_id')
    def _on_product_changed(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id
            self.qty = 1
