__author__ = 'NgaDV'
# -*- coding: utf-8 -*-

from odoo import fields, api, models


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    x_expiration_date_of_supplier = fields.Date(string="Expiration date supplier")