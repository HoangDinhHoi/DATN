# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    type = fields.Selection(selection_add=[('coupon', 'Coupon')])

class PosConfig(models.Model):
    _inherit = 'pos.config'

    journal_ids = fields.Many2many(
        'account.journal', 'pos_config_journal_rel',
        'pos_config_id', 'journal_id', string='Available Payment Methods',
        domain="[('journal_user', '=', True ), ('type', 'in', ['bank', 'cash','coupon'])]",)
