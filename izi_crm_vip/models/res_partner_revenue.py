# -*- coding: utf-8 -*-
# Created by Hoanglv on 10/15/2019

from odoo import fields, models, api


class ResPartnerRevenue(models.Model):
    _name = 'res.partner.revenue'
    _description = 'Res partner revenue'

    @api.one
    def get_date_view(self):
        if self.revenue_date:
            self.revenue_date_view = self.revenue_date.strftime('%m/%Y')

    revenue = fields.Float(string='Revenue')
    revenue_date = fields.Date(string='Date')
    revenue_date_view = fields.Char(string='Date view', compute=get_date_view)
    partner_id = fields.Many2one('res.partner', string='Partner')
