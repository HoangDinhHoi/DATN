# -*- coding: utf-8 -*-

# author: HoiHD

from odoo import fields, models, api, _


class stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'

    def _company_default(self):
        return self.env['res.company']._company_default_get('res.partner')

    x_release_id = fields.Many2one('product.release', string=_('Release Times'))
    x_extend_date = fields.Date(string=_('Extend Date'))
    x_order_id = fields.Many2one('pos.order', string=_('Order'))
    x_order_use_id = fields.Many2one('pos.order', string=_('Order Use'))
    x_company_id = fields.Many2one('res.company', string=_('Company'), default=_company_default)
    x_customer_id = fields.Many2one('res.partner', string=_('Customer'))
    # chuyen doi tac sang chi nhanh: HoiHD
    x_branch_id = fields.Many2one('res.branch', string=_('Partner'))
    # end
    x_use_customer_id =fields.Many2one('res.partner', string=_('User'))
    x_total_count = fields.Integer(string=_('Total Count'), default=1)
    x_used_count = fields.Integer(string=_('Used Count'))
    x_state = fields.Selection([
        ('new', _('New')),
        ('activated', _('Activated')),
        ('using', _('Using')),
        ('used', _('Used')),
        ('destroy', _('Destroy'))
    ], string=_('Status'), default='new')
    life_date = fields.Date(string=_("Life Date"))
    x_stock_production_lot_line_ids = fields.One2many('stock.production.lot.line', 'stock_production_lot_id', string=_('Stock Product Lot Line'))


class StockProductionLotLine(models.Model):
    _name = 'stock.production.lot.line'
    
    product_id = fields.Many2one('product.product', string=_('Product'))
    total_count = fields.Integer(string=_('Total Count'))
    used_count = fields.Integer(string=_('Used Count'))
    stock_production_lot_id = fields.Many2one('stock.production.lot', string=_('Stock Product Lot'))
    price_unit = fields.Float("Price Unit")
    price_sub_total = fields.Float("Price Sub Total")
    remain_sub_total = fields.Float("Remain Sub total")

