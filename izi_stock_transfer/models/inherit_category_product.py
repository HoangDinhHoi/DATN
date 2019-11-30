# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ProductCategory_Inherit(models.Model):
    _inherit = 'product.category'

    x_account_transfer_id = fields.Many2one('account.account', 'Account Transfer', company_dependent=True,
        help="Account Transfer")