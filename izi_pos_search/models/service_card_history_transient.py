# -*- coding: utf-8 -*-

from odoo import models, fields, _


class UseServiceCardDetail(models.TransientModel):
    _name = 'card.service.history.transient'

    search_id = fields.Many2one('pos.search', string=_('Search'))
    using_id = fields.Many2one('pos.use.service', string=_('Using Order'))
    date = fields.Datetime(string=_('Redeem Date'))
    lot_id = fields.Many2one('stock.production.lot', string=_('Card Code'))
    service_id = fields.Many2one('product.product', string=_('Service'))
    qty = fields.Float(string=_("Quantity"))
    price_unit = fields.Float(string=_("Price Unit"))
    amount_total = fields.Float(string=_("Amount Total"))
    employee_ids = fields.Many2many('hr.employee', string=_('Employee'))
    order_id = fields.Many2one('pos.order', string=_('Order'))
    state = fields.Selection([('draft', _("Draft")),
                              ('wait_payment', _("Wait Payment")),
                              ('wait_material', _("Wait Material")),
                              ('working', _("Working")),
                              ('rate', _("Rate")),
                              ('done', _("Done")),
                              ('done_refund', _("Done Refund")),
                              ('cancel', _("Canceled")),
                              ('wait_confirm', _("Wait Confirm")),
                              ('approval', _("Approval"))],
                             default='draft', string=_('State'))
    customer_sign = fields.Binary(string=_('Customer Sign'))
    note = fields.Char(string=_("Note"))
    company_id = fields.Many2one('res.company', string=_('Company'))
