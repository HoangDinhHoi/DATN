# -*-coding:utf-8-*-

from odoo import fields, models, _


class CouponTransient(models.TransientModel):
    _name = 'coupon.transient'

    product_release_id = fields.Many2one('product.release', string=_('Product Release'))
    search_id = fields.Many2one('pos.search', string=_('Search'))
    name = fields.Char(string=_('Name'))
    stk_prdt_lot_id = fields.Many2one('stock.production.lot', string=_('Stock Production Lot'))
    product_id = fields.Many2one('product.product', string=_('Product'))
    order_id = fields.Many2one('pos.order', string=_('Order'))
    customer_id = fields.Many2one('res.partner', string=_('Customer'))
    branch_id = fields.Many2one('res.branch', string=_('Partner'))

    life_date = fields.Date(string=_('Life Date'))
    amount = fields.Float(string=_('Amount'))
    discount = fields.Float(string=_('Discount'))
    state = fields.Selection([
        ('new', _('New')),
        ('activated', _('Activated')),
        ('using', _('Using')),
        ('used', _('Used')),
        ('destroy', _('Destroy'))
    ])
    order_use_id = fields.Many2one('pos.order', string=_('Order Payment'))
    use_customer_id = fields.Many2one('res.partner', string=_('Use Customer'))
    use_date = fields.Date(string=_('Use Date'))
    company_id = fields.Many2one('res.company', string=_('Company'))


