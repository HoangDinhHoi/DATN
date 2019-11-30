# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/9/2019

from odoo import models, fields, api, _


class PartnerSource(models.Model):
    _name = 'partner.source'

    name = fields.Char(string='Source name')
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Resource code must be unique')
    ]
