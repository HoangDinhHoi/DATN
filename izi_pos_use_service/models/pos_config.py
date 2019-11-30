# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    module_izi_pos_request_material = fields.Boolean("Request Material" ,default=False)
    # x_material_picking_type_id = fields.Many2one('stock.picking.type', "Material Picking Type")
    material_location_id = fields.Many2one('stock.location', "Material Location")


