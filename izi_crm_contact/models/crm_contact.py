# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm

from addons_custom.izi_utilities.phone_number import PhoneNumber


class CrmContact(models.Model):
    _name = 'crm.contact'
    _description = 'Crm Contact'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_team(self):
        pos_session = self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)
        return pos_session.config_id.crm_team_id.id

    def _default_company_id(self):
        company_id = False
        if self._context.get('default_department_id'):
            department = self.env['hr.department'].browse(self._context['default_department_id'])
            company_id = department.company_id.id
        if not company_id:
            company_id = self.env['res.company']._company_default_get('hr.applicant')
        return company_id

    name = fields.Char(string="Name", track_visibility='onchange')
    phone = fields.Char(string="Phone", track_visibility='onchange')
    mobile = fields.Char(string="Mobile")
    email = fields.Char(string="Email")
    brand_id = fields.Many2one('res.brand', string='Brand', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', "Partner")
    user_id = fields.Many2one('res.users', "User", track_visibility='onchange')
    team_id = fields.Many2one('crm.team', "Team", default=_default_team, track_visibility='onchange')
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")
    state_id = fields.Many2one('res.country.state', "Country State")
    country_id = fields.Many2one('res.country', "Country")
    source_id = fields.Many2one('partner.source', "Source")
    join_date = fields.Date(string='Join Date', default=fields.Date.today())
    presenter_id = fields.Many2one('res.partner', string='Presenter')
    company_id = fields.Many2one('res.company', "Company", default=_default_company_id, track_visibility='onchange')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('phone_uniq', 'unique(phone, brand_id)', 'The phone of this Contact must be unique!')
    ]

    @api.constrains('phone', 'mobile')
    def _check_phone_mobile(self):
        try:
            if self.phone:
                PhoneNumber.validate_phone_number(self.phone, 'Số điện thoại phải bắt đầu từ số 0 và có 10 chữ số.')
            if self.mobile:
                PhoneNumber.validate_phone_number(self.mobile, 'Số di động phải bắt đầu từ số 0 và có 10 chữ số.')
        except Exception as e:
            raise except_orm(_('Thông báo'), str(e))

    @api.multi
    def action_create_partner(self):
        view = self.env.ref('base.view_partner_form')
        partner = self.create_partner()
        return {
            'name': 'Partner',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.partner',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'res_id': partner.id,
            'context': self._context.copy(),
        }

    def create_partner(self):
        vals = {
            'name': self.name,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': self.email,
            'brand_id': self.brand_id.id,
            'user_id': self.user_id.id if self.user_id else False,
            'team_id': self.team_id.id if self.team_id else False,
            'street': self.street,
            'street2': self.street2,
            'state_id': self.state_id.id if self.state_id else False,
            'presenter_id': self.presenter_id.id if self.presenter_id else False,
            'country_id': self.country_id.id if self.country_id else False,
            'source_id': self.source_id.id if self.source_id else False,
            'company_id': self.company_id.id if self.company_id else False,
            'customer': True
        }
        partner = self.env['res.partner'].with_context(create_from_contact=True).create(vals)
        self.partner_id = partner.id
        return partner
