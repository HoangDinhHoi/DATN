# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date

class Account(models.Model):
    _inherit = 'account.account'

    @api.multi
    @api.depends('name', 'code','company_id')
    def name_get(self):
        result = []
        for account in self:
            if account.company_id.partner_id.x_partner_code:
                name = '[' + str(account.company_id.partner_id.x_partner_code) + ']' + account.code + ' ' + account.name
            else:
                name = account.code + ' ' + account.name
            result.append((account.id, name))
        return result

