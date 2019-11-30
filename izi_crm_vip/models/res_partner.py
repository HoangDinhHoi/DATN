# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm

from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_partner_revenue_domain(self):
        revenue_date = (fields.Date.today() - relativedelta(months=13)).strftime('%Y-%m-01')
        return [('revenue_date', '>=', revenue_date)]

    x_rank_id = fields.Many2one('crm.customer.rank', "Rank")
    partner_revenue_ids = fields.One2many('res.partner.revenue', 'partner_id', string='Partner revenue',
                                          domain=_get_partner_revenue_domain)
    history_ids = fields.One2many('partner.rank.history', 'partner_id', string='Up rank history',
                                  domain=[('state', '!=', 'auto')])

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if not res.x_rank_id and res.customer:
            code_rank_5TH = '5TH'
            rank_5TH = self.env['crm.customer.rank'].search([('code', '=', code_rank_5TH)], limit=1)
            if not rank_5TH:
                raise except_orm('Thông báo!', ('Hạng khách hàng thường (5TH) chưa được cấu hình. Vui lòng cấu hình trước khi tạo khách hàng'))
            res.with_context(no_sync=True).x_rank_id = rank_5TH.id
        return res