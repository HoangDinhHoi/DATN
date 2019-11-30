# -*- coding: utf-8 -*-
# Created by Hoanglv on 10/25/2019

from odoo import api, fields, models


class PartnerRankHistoryExtend(models.Model):
    _name = 'partner.rank.history.extend'
    _description = 'Partner rank history extend'
    _order = 'create_date ASC'

    rank_id = fields.Many2one('crm.customer.rank', string='Rank')
    extend_date = fields.Date(string='Extend date')
    year_extend = fields.Float(string='Extend year')
    partner_vip_id = fields.Many2one('res.partner.vip', string='Partner VIP')
