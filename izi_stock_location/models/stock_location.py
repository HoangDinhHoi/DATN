# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm



class StockLocation(models.Model):
    _inherit = 'stock.location'

    x_code = fields.Char('Code')

    _sql_constraints = [
        ('x_code_uniq', 'unique(x_code)', _('The code must be unique!'))]

    @api.onchange('x_code')
    def _onchange_x_code(self):
        if self.x_code:
            if ' ' in self.x_code:
                raise except_orm('Warning!', _('The code do not allow any space!'))
            self.x_code = self.x_code.upper().strip()

    def name_get(self):
        ret_list = []
        for location in self:
            if location.x_code:
                name = '[' + location.x_code + "]" + location.name
                ret_list.append((location.id, name))
            else:
                orig_location = location
                name = location.name
                while location.location_id and location.usage != 'view':
                    location = location.location_id
                    if not name:
                        raise UserError(_('You have to set a name for this location.'))
                    name = location.name + "/" + name
                ret_list.append((orig_location.id, name))
        return ret_list

    
    
