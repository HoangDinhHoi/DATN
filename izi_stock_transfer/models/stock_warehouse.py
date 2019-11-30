# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    x_wh_transfer_loc_id = fields.Many2one('stock.location', 'Transfer Location')
    user_id = fields.Many2one('res.users', string='Stockkeeper')
    user_ids = fields.Many2many('res.users', string='Users')

    @api.model
    def create(self, vals):
        res = super(Warehouse, self).create(vals)
        sub_locations = {
            'x_wh_transfer_loc_id': {'name': _('Transfer'), 'active': True, 'usage': 'transit'},
        }
        for field_name, values in sub_locations.items():
            values['location_id'] = vals['view_location_id']
            if vals.get('company_id'):
                values['company_id'] = vals.get('company_id')
            transfer_loc_id = self.env['stock.location'].with_context(active_test=False).create(values).id
            res.update({field_name:transfer_loc_id})
        return res

class StockLocation(models.Model):
    _inherit = "stock.location"

    def _should_be_valued(self):
        """ This method returns a boolean reflecting whether the products stored in `self` should
        be considered when valuating the stock of a company.
        """
        self.ensure_one()
        if self.usage == 'internal':
            return True
        return False
