# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm, ValidationError

from addons_custom.izi_utilities.phone_number import PhoneNumber

STATE_SELECTOR = [('new', 'New'), ('assigned', 'Assigned'), ('won', 'Won'), ('dead', 'Dead')]


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    contact_id = fields.Many2one('crm.contact', "Contact")
    brand_id = fields.Many2one('res.brand', string='Brand')
    register_time = fields.Datetime(string='Register Time', default=fields.Datetime.now())
    datetime_assigned = fields.Datetime(string='Datetime assigned')
    date_of_birth = fields.Date('Date of Birth')
    account_facebook = fields.Char(string="Account Facebook")
    product_quotation_ids = fields.One2many('crm.lead.quotation', 'lead_id', 'Product Quotation')
    serial_ids = fields.One2many('crm.lead.serial', 'crm_lead_id', 'Serial')
    crm_lead_ids = fields.One2many(related='contact_id.crm_lead_ids', readonly=True, string='CRM Leads')
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange', track_sequence=1,
                                 index=True, related='contact_id.partner_id', store=True,
                                 help="Linked partner (optional). Usually created when converting the lead. "
                                      "You can find a partner by its Name, TIN, Email or Internal Reference.")
    team_id = fields.Many2one('crm.team', string='Sales Team', oldname='section_id',
                              default=False, index=True, track_visibility='onchange',
                              help='When sending mails, the default email address is taken from the Sales Team.')
    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange', default=False)
    tool_id = fields.Many2one('utm.source', string='Tool')
    source_id = fields.Many2one('partner.source', string='Source')
    state = fields.Selection(STATE_SELECTOR, default="new", string="State", track_visibility='onchange')

    @api.onchange('phone', 'brand_id')
    def _onchange_phone_brand_id(self):
        if self.phone and self.brand_id:
            CrmContact = self.env['crm.contact']
            contact = CrmContact.search([('phone', '=', self.phone), ('brand_id.code', '=', 'all')], limit=1)
            if not contact:
                contact = CrmContact.search([('phone', '=', self.phone), ('brand_id', '=', self.brand_id.id)])
            if contact:
                self.contact_id = contact.id

    @api.constrains('phone', 'mobile')
    def _constraint_phone_mobile(self):
        self.__validate_phone_mobile(self.phone, self.mobile)

    @api.onchange('campaign_id')
    def _onchange_campaign_id(self):
        if self.campaign_id:
            self.source_id = self.campaign_id.source_id
        else:
            self.source_id = False

    @api.constrains('contact_id')
    def _constraint_contact_id(self):
        if self.contact_id and self.contact_id.partner_id:
            self.partner_id = self.contact_id.partner_id
            self.name = self.contact_id.partner_id.name

    @api.constrains('state')
    def _constraint_state(self):
        if self.state and self.state == 'assigned':
            self.datetime_assigned = fields.Datetime.now()

    @api.multi
    def action_open_assign_dialog(self):
        return self.env['crm.lead.assign'].with_context(active_id=self.id).get_assign_dialog()

    @api.multi
    def action_open_reassign_dialog(self):
        return self.env['crm.lead.assign'].with_context(active_id=self.id).get_reassign_dialog()

    @api.multi
    def action_dead(self):
        self.state = 'dead'

    @staticmethod
    def __validate_phone_mobile(phone=False, mobile=False):
        try:
            if phone:
                PhoneNumber.validate_phone_number(phone, 'Phone number must be start with "0" and it\'s length '
                                                         'between 10 and 11')
            if mobile:
                PhoneNumber.validate_phone_number(mobile, 'Mobile number must be start with "0" and it\'s length '
                                                          'between 10 and 11')
        except Exception as e:
            raise ValidationError(str(e))
