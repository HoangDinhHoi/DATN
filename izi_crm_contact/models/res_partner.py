# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if res.phone:
            contact = self.env['crm.contact'].search([('phone', '=', res.phone), ('brand_id', '=', res.brand_id.id)])
            if not self._context.get('create_from_contact', False):
                if not contact:
                    res.__create_contact()
                elif not contact.partner_id:
                    contact.partner_id = res.id
                else:
                    raise except_orm(_('Cảnh báo'), _('Không thể tạo khách hàng vì số điên thoại đã tồn tại trong '
                                                      'contact %s.' % contact.name))
        return res

    def __create_contact(self):
        vals = {'name': self.name,
                'phone': self.phone,
                'mobile': self.mobile,
                'email': self.email,
                'brand_id': self.brand_id.id if self.brand_id else False,
                'partner_id': self.id,
                'user_id': self.user_id.id if self.user_id else False,
                'team_id': self.team_id.id if self.team_id else False,
                'street': self.street,
                'street2': self.street2,
                'state_id': self.state_id.id if self.state_id else False,
                'country_id': self.country_id.id if self.country_id else False,
                'source_id': self.source_id.id if self.source_id else False,
                'join_date': self.join_date,
                'presenter_id': self.presenter_id.id if self.presenter_id else False,
                'company_id': self.company_id.id if self.company_id else False}
        return self.env['crm.contact'].create(vals)

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if not self._context.get('contact'):
            context = dict(self._context or {})
            context['partner'] = True
            crm_contact_obj = self.env['crm.contact'].search([('partner_id', '=', self.id)],limit=1)
            if crm_contact_obj:
                crm_contact_obj.with_context(context).update({
                    'phone': self.phone,
                    'mobile': self.mobile,
                    'street': self.street,
                    'street2': self.street2,
                    'state_id': self.state_id.id,
                    'country_id': self.country_id.id,
                    'team_id': self.team_id.id,
                    'user_id': self.user_id.id,
                })
        return res
