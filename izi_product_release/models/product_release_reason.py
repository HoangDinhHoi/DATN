# -*- coding: utf-8 -*-
# author: HoiHD
# That's Reason to public a card
from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class product_release_reason(models.Model):
    _name = 'product.release.reason'
    
    code = fields.Char(string=_('Code'))
    release_reason_type = fields.Integer(string=_('Type'))
    description = fields.Char(string=_('Description'))
    name = fields.Char(string=_('Name'))
    
    @api.model
    def create(self, vals):
        if 'code' in vals:
            my_code = self.env['product.release.reason'].search([('code', '=', vals.get('code').strip().upper())])
            if my_code:
                raise except_orm('Warning!!!', 'Code has existed! Please choose other code.')
            vals['code'] = vals.get('code').strip().upper()
        return super(product_release_reason, self).create(vals)
    
    @api.multi
    def write(self, vals):
        if vals.get('code') and vals.get('code') != '':
            my_code = self.env['product.release.reason'].search([('code', '=', vals.get('code').strip().upper())])
            if my_code:
                raise except_orm('Warning!!!', 'Code has existed! Please choose other code.')
            vals['code'] = vals.get('code').strip().upper()
        return super(product_release_reason, self).write(vals)