# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError

import logging

from addons_custom.izi_utilities.phone_number import PhoneNumber

_logger = logging.getLogger(__name__)

SEX_SELECTOR = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _name = 'res.partner'

    team_id = fields.Many2one('crm.team', string='Sales Team', oldname='section_id',
                              default=lambda self: self.env.user.sale_team_id.id)
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user.id,
                              help='The internal user in charge of this contact.')
    x_partner_code = fields.Char(string="Partner code")
    x_partner_old_code = fields.Char(string="Partner old code")
    x_is_shop = fields.Boolean(string=_('Is a Shop'), help=_("Check this box if this contact is a shop."))
    join_date = fields.Date(string='Join Date', default=fields.Date.today())
    brand_id = fields.Many2one('res.brand', string='Brand')
    presenter_id = fields.Many2one('res.partner', string='Presenter')
    x_gender = fields.Selection(SEX_SELECTOR, string='Sex', default='male')
    x_birthday = fields.Date(string='Birthday')

    _sql_constraints = [
        ('x_partner_code_uniq', 'unique (x_partner_code)', 'The new code of this Partner must be unique !'),
        ('x_partner_old_code_uniq', 'unique (x_partner_old_code)', 'The old code of this Partner must be unique !'),
        ('phone_uniq', 'unique (phone, brand_id)', 'The phone of this Partner must be unique !'),
        ('mobile_uniq', 'unique (mobile, brand_id)', 'The mobile of this Partner must be unique !'),
    ]

    @api.constrains('phone', 'mobile')
    def _check_phone_mobile(self):
        context = self._context
        if self.customer and 'import_data_vmt1' not in context:
            try:
                if self.phone:
                    PhoneNumber.validate_phone_number(self.phone, 'Phone number must be start with "0" and '
                                                                  'it\'s length between 10 and 11')
                if self.mobile:
                    PhoneNumber.validate_phone_number(self.mobile, 'Mobile number must be start with "0" and '
                                                                   'it\'s length between 10 and 11')
            except Exception as e:
                raise ValidationError(str(e))

    @api.depends('name', 'x_partner_code', 'x_partner_old_code')
    def _compute_display_name(self):
        for partner in self:
            name = partner.name or ''
            if partner.x_partner_code:
                name = '[' + partner.x_partner_code + ']' + name
            elif partner.x_partner_old_code:
                name = '[' + partner.x_partner_old_code + ']' + name
            partner.display_name = name

    @api.model
    def create(self, vals):
        website = self._clean_website(vals.get('website')) if vals.get('website') else ''
        brand_id = vals.get('brand_id', '')
        x_partner_code = vals.get('x_partner_code', '')
        x_partner_old_code = vals.get('x_partner_old_code', '')
        if not x_partner_code:
            x_partner_code = self._generate_customer_code_v2(vals)
        if not x_partner_old_code:
            x_partner_old_code = x_partner_code
        if not brand_id:
            brand_id = self.env['res.brand'].search([('code', '=', 'menard')]).id

        if vals.get('employee', False) and self._context.get('x_emp_code'):
            x_partner_code = x_partner_old_code = 'NV%s' % self._context.get('x_emp_code')

        if not vals.get('mobile', ''):
            vals.update({'mobile': vals.get('phone')})

        vals.update({'website': website,
                     'brand_id': brand_id,
                     'x_partner_code': x_partner_code.strip().upper(),
                     'x_partner_old_code': x_partner_old_code.strip().upper()})
        return super(ResPartner, self).create(vals)

    def _generate_customer_code_v2(self, vals):
        SequenceObj = self.env['ir.sequence']
        context = {'force_company': 1}
        if vals.get('is_company'):
            return SequenceObj.with_context(**context).next_by_code('company_code')

        if vals.get('supplier'):
            return SequenceObj.with_context(**context).next_by_code('supplier_code')

        if vals.get('x_is_shop'):
            if vals.get('x_partner_old_code') == '':
                raise except_orm('Thông báo', 'Bắt buộc phải nhập mã nội bộ khi tạo shop.')
            return vals.get('x_partner_old_code')

        if vals.get('customer'):
            if vals.get('company_id'):
                company = self.env['res.company'].search([('id', '=', vals.get('company_id')),
                                                          ('partner_id.x_partner_old_code', '!=', 'TCT')])
                if company:
                    return SequenceObj.with_context(**context).next_by_code('franchise_code')

            return SequenceObj.with_context(**context).next_by_code('customer_seq')

        return SequenceObj.with_context(**context).next_by_code('user_code')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        context = self._context
        UserObj = self.env['res.users']
        user = UserObj.search([('id', '=', self._uid)], limit=1)
        result = []
        domain = args + ['|', '|','|', ('name', 'ilike', name), ('x_partner_old_code', '=ilike', name), ('phone', '=ilike', name), ('mobile', '=ilike', name)]
        if 'force_company' in context and context['force_company'] == 1:
            domain = domain
        else:
            domain += [('company_id', 'in', user.company_ids.ids)]
        partners = self.search_read(domain, fields=['id', 'x_partner_old_code', 'name'], limit=limit)
        if partners:
            for partner in partners:
                result.append([partner['id'], '[' + str(partner['x_partner_old_code']) + '] ' + str(partner['name'])])
        elif 'limit_company' in context and context['limit_company']:
            partners = self.search_read(['|',('phone', '=', name),('mobile', '=', name)], fields=['id', 'x_partner_old_code', 'name'], limit=limit)
            for partner in partners:
                result.append([partner['id'], '[' + str(partner['x_partner_old_code']) + '] ' + str(partner['name'])])
        res = result
        return res
