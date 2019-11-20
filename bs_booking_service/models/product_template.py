# -*- coding: utf-8 -*-
__author__ = "HoiHD"

import logging
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_duration = fields.Float(string='Thời lượng', default=0)

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code)', _('The code must be unique!'))]
