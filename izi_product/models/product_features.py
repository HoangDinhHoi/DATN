# -*- coding: utf-8 -*-
# author: Tant
from odoo import fields, models, api, _
from odoo.exceptions import except_orm


class product_feautures(models.Model):
    _name = 'product.features'

    name = fields.Char(string=_('Name'))
    code = fields.Char(string=_('Code'))
    description = fields.Text(string=_('Description'))
    active = fields.Boolean(string=_('Active'), default=True)

    _sql_constraints = [('uniq_code', 'unique(code)', "The code of this product features must be unique !")]

    @api.onchange('code')
    def _onchange_code(self):
        if self.code:
            if ' ' in self.code:
                raise except_orm('Warning!', _('The code do not allow any space!'))
            self.code = self.code.upper().strip()

