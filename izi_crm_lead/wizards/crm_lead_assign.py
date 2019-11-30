# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/7/2019

from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class CrmLeadAssign(models.TransientModel):
    _name = 'crm.lead.assign'

    user_id = fields.Many2one('res.users', string='User')
    team_id = fields.Many2one('crm.team', string='Sales Team')
    override = fields.Boolean(string='Override', default=False,
                              help='If check this, when save record this will be override content '
                                   'of record has exist value')

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            team_id = self.user_id.sale_team_id.id if self.user_id.sale_team_id else False
            return {'domain': {'team_id': [('id', '=', team_id)]}}
        else:
            return {'domain': {'team_id': []}}

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            return {'domain': {'user_id': [('id', 'in', self.team_id.member_ids.ids)]}}
        else:
            return {'domain': {'user_id': []}}

    @api.multi
    def action_assign(self):
        lead_id = self._context.get('active_id')
        self.__assign(lead_id, self.user_id.id, self.team_id.id, True, ['new'])
        return self.env['message.dialog'].show_dialog('Thông báo', 'Giao lead thành công')

    @api.multi
    def action_reassign(self):
        lead_id = self._context.get('active_id')
        self.__assign(lead_id, self.user_id.id, self.team_id.id, True, ['assigned', 'contact'])
        return self.env['message.dialog'].show_dialog('Thông báo', 'Giao lead thành công')

    @api.multi
    def action_assign_multi(self):
        lead_ids = self._context.get('active_ids')
        for lead_id in lead_ids:
            self.__assign(lead_id, self.user_id.id, self.team_id.id, self.override)
        return self.env['message.dialog'].show_dialog('Thông báo', 'Giao lead thành công')

    def __assign(self, lead_id, user_id, team_id, override=True, states=['new', 'assigned', 'contact']):
        lead = self.env['crm.lead'].browse(lead_id)
        team = self.env['crm.team'].browse(team_id)
        if lead.state not in states:
            raise except_orm('Cảnh báo', 'Không thể giao lại ở trạng thái %s' % lead.state)
        if override:
            self.__update_contact(lead, team, user_id, team_id)
            lead.write({'user_id': user_id,
                        'team_id': team_id,
                        'company_id': team.company_id.id,
                        'state': 'assigned'})

    def __update_contact(self, lead, team, user_id, team_id):
        if not lead.contact_id:
            contact = self.__create_contact(lead, team)
            lead.write({'contact_id': contact.id})
        else:
            lead.contact_id.write({'user_id': user_id,
                                   'team_id': team_id,
                                   'active': True})

    def __create_contact(self, lead, team):
        vals = {'name': lead.name,
                'phone': lead.phone,
                'mobile': lead.mobile if lead.mobile else lead.phone,
                'email': lead.email_from,
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'street': lead.street,
                'street2': lead.street2,
                'date_of_birth': lead.date_of_birth,
                'source_id': lead.source_id.id if lead.source_id else False,
                'brand_id': lead.brand_id.id if lead.brand_id else False,
                'state_id': lead.state_id.id if lead.state_id else False,
                'country_id': lead.country_id.id if lead.country_id else False,
                'company_id': team.company_id.id if team.company_id else False}
        return self.env['crm.contact'].create(vals)

    def get_assign_dialog(self):
        view = self.env.ref('izi_crm_lead.assign_lead_dialog')
        return self.with_context(assign=True).__get_action_view(view, 'Giao lead')

    def get_reassign_dialog(self):
        lead_id = self._context.get('active_id')
        lead = self.env['crm.lead'].browse(lead_id)
        view = self.env.ref('izi_crm_lead.assign_lead_dialog')
        return self.with_context(reassign=True,
                                 default_user_id=lead.user_id.id,
                                 default_team_id=lead.team_id.id).__get_action_view(view, 'Giao lại lead')

    def get_assign_multi_dialog(self):
        view = self.env.ref('izi_crm_lead.assign_lead_dialog')
        return self.with_context(assign_multi=True).__get_action_view(view, 'Giao nhiều lead')

    def __get_action_view(self, view, name):
        ctx = self._context.copy()
        ctx.update({'dialog_size': 'medium'})
        return {
            'name': _(name),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.assign',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }
