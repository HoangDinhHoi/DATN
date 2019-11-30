# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ResBrand(models.Model):
    _name = 'res.brand'

    name = fields.Char(string='Name')
    code = fields.Char(string='code')
    description = fields.Text(string='Description')

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Code must be unique')
    ]
