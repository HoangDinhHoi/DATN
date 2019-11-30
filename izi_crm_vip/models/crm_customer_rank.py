# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmCustomerRank(models.Model):
    _name = 'crm.customer.rank'
    _description = 'Rank'
    _order = 'level asc'

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    active = fields.Boolean(string="Active", default=True)
    level = fields.Integer(string="Level")
    active_month = fields.Integer(string="Active Mont")
    policy = fields.Html(string="Policy")
    discount_service = fields.Float(string="Discount Service")
    discount_product = fields.Float(string="Discount Product")
    except_product_ids = fields.One2many('crm.customer.rank.product.except', 'rank_id', 'Except products')



