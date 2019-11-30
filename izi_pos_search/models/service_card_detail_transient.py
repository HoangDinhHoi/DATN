# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ServiceCardDetail(models.TransientModel):
    _name = 'card.service.detail.transient'

    product_release_id = fields.Many2one('product.release', string=_('Product Release'))
    search_id = fields.Many2one('pos.search', string=_('Search'))
    name = fields.Char(string=_('Name'))
    stk_prdt_lot_id = fields.Many2one('stock.production.lot', string=_('Stock Production Lot'))
    product_id = fields.Many2one('product.product', string=_('Product'))
    order_id = fields.Many2one('pos.order', string=_('Order'))
    customer_id = fields.Many2one('res.partner', string=_('Customer'))
    branch_id = fields.Many2one('res.branch', string=_('Partner'))
    life_date = fields.Date(string='Life Date')
    state = fields.Selection([
        ('new', _('New')),
        ('activated', _('Activated')),
        ('using', _('Using')),
        ('used', _('Used')),
        ('destroy', _('Destroy'))
    ])
    service_id = fields.Many2one('product.product', string=_('Service'))
    total_count = fields.Integer(string=_('Total Count'))
    used_count = fields.Integer(string=_('Used Count'))
    residual_count = fields.Integer(string=_('Residual Count'))
    price_unit = fields.Float(string=_("Price Unit"))
    price_sub_total = fields.Float(string=_("Price Sub Total"))
    remain_sub_total = fields.Float(string=_("Remain Sub total"))
    company_id = fields.Many2one('res.company', string=_('Company'))


