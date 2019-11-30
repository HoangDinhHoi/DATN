# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_recipe_ids = fields.One2many('product.recipe.line', 'product_recipe_id', "Recipe Line")
    x_is_use_material = fields.Boolean("Use Material", default=True)