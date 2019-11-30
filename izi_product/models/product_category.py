# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import except_orm


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_account_discount_vip_categ_id = fields.Many2one('account.account', company_dependent=True,
                                                       string="Discount VIp Account",
                                                       domain=[('deprecated', '=', False)],)

    property_account_discount_tm_categ_id = fields.Many2one('account.account', company_dependent=True,
                                                             string="Discount TM Account",
                                                             domain=[('deprecated', '=', False)],)
    revenue_deduction = fields.Boolean("Revenue Deduction", default=False)

    #Tant thêm
    x_code = fields.Char(string=_('Code'))



    _sql_constraints = [('uniq_x_code', 'unique(x_code)', "The code of this product features must be unique !")]

    @api.onchange('x_code')
    def _onchange_x_code(self):
        if self.x_code:
            if ' ' in self.x_code:
                raise except_orm('Warning!', _('The code do not allow any space!'))
            self.x_code = self.x_code.upper().strip()

