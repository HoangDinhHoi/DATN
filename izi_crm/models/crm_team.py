# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm
import re


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    x_code = fields.Char("Code")
    x_show_in_app = fields.Boolean(string='Show in app', default=False)

    _sql_constraints = [('uniq_code', 'unique(x_code)', "The code of this Crm Team must be unique !")]

    @api.model
    def create(self, vals):
        if 'x_code' in vals and vals['x_code'] and len(vals['x_code']):
            regex = r'^[a-zA-Z0-9]*$'
            ob = re.search(regex, vals.get('x_code').upper())
            if ob == None:
                raise except_orm("Thông báo", ('Có ký tự đặc biệt trong mã. Vui lòng kiểm tra lại!'))
            if len(self.env['crm.team'].search([('x_code', '=', vals['x_code'].upper())])) != 0:
                raise except_orm('Thông báo', ("The code you entered already exists"))
            if ' ' in vals.get('x_code'):
                raise except_orm('Thông báo', ("No spaces allowed in Code input"))
            vals['x_code'] = vals.get('x_code').upper()
        return super(CrmTeam, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get("x_code") != None:
            regex = r'^[a-zA-Z0-9]*$'
            ob = re.search(regex, vals.get('x_code').upper())
            if ob == None:
                raise except_orm("Thông báo", ('Có ký tự đặc biệt trong mã. Vui lòng kiểm tra lại!'))
            if len(self.env['crm.team'].search([('x_code', '=', vals.get("x_code").upper())])) != 0:
                raise except_orm('Thông báo', ("The code you entered already exists"))
            if ' ' in vals.get('x_code'):
                raise except_orm('Thông báo', ("No spaces allowed in Code input"))
            vals['x_code'] = vals.get('x_code').upper()
        res = super(CrmTeam, self).write(vals)
        return res


