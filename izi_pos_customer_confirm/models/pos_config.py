# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    module_izi_pos_customer_confirm = fields.Boolean(default=True)