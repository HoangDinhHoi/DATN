# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError
from datetime import datetime, date

WARNING = 'Thông báo!'


class PosRuleCardExpirate(models.Model):
    _name = 'pos.rule.card.expirate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default='Quy tắc hạn thẻ')
    start_date = fields.Date("Start Date", track_visibility='onchange')
    end_date = fields.Date("End Date", track_visibility='onchange')
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    rule_ids = fields.One2many('pos.rule.card.expirate.line','rule_id',string='Rules')

    @api.constrains('start_date','end_date')
    def _constrains_date(self):
        for item in self:
            if item.end_date <= item.start_date:
                raise except_orm('Thông báo', ('Ngày kết thúc phải lớn hơn ngày bắt đầu'))

    def _compute_month(self, type, count):
        month = 0
        for line in self.rule_ids:
            if line.type == type and line.min_qty <= count and line.max_qty >= count:
                month = line.month
        if month == 0:
            raise except_orm('Thông báo', ('Có vấn đề về quy tắc hạn thẻ. Vui lòng liện hệ quản trị viên.'))
        return month


class PosRuleCardExpirateLine(models.Model):
    _name = 'pos.rule.card.expirate.line'

    type = fields.Selection(selection=[('keep_card', 'Keep Card'),('service_card', 'Service Card')], string='Type Card',track_visibility='onchange')
    min_qty = fields.Integer('Min Qty')
    max_qty = fields.Integer('Max Qty')
    month = fields.Integer('Month Expirate')
    rule_id = fields.Many2one('pos.rule.card.expirate',string='Rule')


