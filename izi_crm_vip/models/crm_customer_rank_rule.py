# -*- coding: utf-8 -*-
# Created by Hoanglv on 10/25/2019

from odoo import fields, models, api

from datetime import datetime
from dateutil.relativedelta import relativedelta

STATE_SELECTOR = [('active', 'Active'), ('deactive', 'Deactive')]
TYPE_SELECTOR = [('extend', 'Extend'), ('up', 'Up rank'), ('keep', 'Keep rank')]
DF = '%Y-%m-%d'


class CrmCustomerRankRule(models.Model):
    _name = 'crm.customer.rank.rule'
    _description = 'Customer rank rule'

    name = fields.Char(string='Name')
    rank_id = fields.Many2one('crm.customer.rank', string='Rank', required=True)
    type = fields.Selection(TYPE_SELECTOR, string='Type', default='up', required=True)
    duration_year = fields.Integer(string='Duration year')
    target_revenue = fields.Integer(string='Target revenue', required=True)
    description = fields.Text(string='Description')
    ranks_allowed = fields.Many2many('crm.customer.rank', string='Rank allowed', required=True)
    brand_id = fields.Many2one('res.brand', string='Brand', required=True)
    state = fields.Selection(STATE_SELECTOR, string='State', default='active', required=True)

    @api.multi
    def action_active(self):
        self.state = 'active'

    @api.multi
    def action_deactive(self):
        self.state = 'deactive'

    def get_year_extend_and_revenue(self, partner_id, date_extend):
        PartnerRankConfirm = self.env['partner.rank.confirm']
        PartnerRankHistory = self.env['partner.rank.history']
        last_history = PartnerRankHistory.get_last_history(partner_id=partner_id)
        if not last_history or (last_history and (not last_history.to_rank or last_history.to_rank != self.rank_id)
                                or date_extend > last_history.up_rank_expired_date):
            return {
                'year': 0,
                'loyal_point': 0,
            }

        today = date_extend.strftime(DF) if date_extend else datetime.today().strftime(DF)
        from_date = (datetime.strptime(today, DF) - relativedelta(months=12)).strftime('%Y-%m-01')
        if last_history.extend_date:
            if datetime.strptime(last_history.extend_date, DF) > datetime.strptime(today, DF) - relativedelta(years=1):
                from_date = last_history.extend_date.strftime(DF)
        else:
            confirm = PartnerRankConfirm.search([('history_id', '=', last_history.id),
                                                 ('type', 'not in', ['extend', 'auto_extend', 'extend_exception'])],
                                                limit=1)
            if confirm and datetime.strptime(confirm.register_date, DF) > datetime.strptime(today, DF) - relativedelta(years=1):
                from_date = confirm.register_date.strftime(DF)
            elif datetime.strptime(last_history.up_rank_date, DF) > datetime.strptime(today, DF) - relativedelta(years=1):
                from_date = last_history.up_rank_date.strftime(DF)

        get_customer_revenue = "SELECT SUM(revenue) AS total_revenue " \
                               "FROM res_partner_revenue " \
                               "WHERE revenue_date BETWEEN %s AND %s AND partner_id = %s"
        self._cr.execute(get_customer_revenue, (from_date, today, partner_id,))
        res = self._cr.dictfetchone()

        return {
            'year': res.get('total_revenue', 0) // self.target_revenue,
            'revenue': res.get('total_revenue', 0),
        }
