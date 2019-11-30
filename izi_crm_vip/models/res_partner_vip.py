# -*- coding: utf-8 -*-
from odoo import models, fields, api

SELECTION = [('pending', 'Pending'), ('qualify', 'Qualify'), ('active', 'Active'), ('deactive', 'Deactive')]

NOTE_DATA = {'': '',
             'pending': 'Khách hàng này cần chờ xác nhận mới có thể lên hạng',
             'suspend': 'Khách hàng đang ở trạng thái treo hạng, cần chờ xác nhận để chính thức lên hạng',
             'done': '',
             'deny': 'Yêu cầu lên hạng của khách hàng này đã bị từ chối'}

QUERY_GET_RESIDUAL = """SELECT SUM(residual) residual 
                            FROM account_invoice 
                            WHERE partner_id = %s 
                                and state='open'"""
QUERY_GET_STATE_NOTE = """Select state 
                            from partner_rank_history 
                            where partner_vip_id = %s 
                            order by create_date desc 
                            limit 1"""


class ResPartnerVip(models.Model):
    _name = 'res.partner.vip'
    _description = 'Partner vip'

    @api.one
    @api.depends('history_ids', 'history_ids.state')
    def _get_state_vip(self):
        history_obj = self.env['partner.rank.history']
        last_history = history_obj.get_last_history(partner_vip_id=self.id)
        state = 'pending'
        if last_history:
            if last_history.to_rank.id == self.partner_id.x_rank_id.id and last_history.state == 'done':
                state = 'active'
            elif last_history.state == 'done':
                state = 'deactive'
        else:
            res = self.env['partner.rank.confirm'].search([('partner_vip_id', '=', self.id),
                                                           ('state', 'in', ['new', 'confirm'])])
            if not res:
                state = 'qualify'
        self.state = state

    @api.one
    def _calc_total_residual(self):
        self._cr.execute(QUERY_GET_RESIDUAL, (self.partner_id.id,))
        res = self._cr.dictfetchone()
        total = res['residual'] if res else 0.0
        self.credit = total

    @api.one
    def _get_up_rank_date(self):
        last_history = self.env['partner.rank.history'].get_last_history(partner_vip_id=self.id)
        self.up_rank_date = last_history.up_rank_date if last_history else None

    @api.one
    def _get_up_rank_expired_date(self):
        last_history = self.env['partner.rank.history'].get_last_history(partner_vip_id=self.id)
        self.up_rank_expired_date = last_history.up_rank_expired_date if last_history else None

    @api.one
    def _get_last_profile_img(self):
        last_history = self.env['partner.rank.history'].get_last_history(partner_vip_id=self.id)
        self.last_profile_img = last_history.profile_img_attachment_id.datas if last_history else None

    @api.one
    def _get_last_form_img(self):
        last_history = self.env['partner.rank.history'].get_last_history(partner_vip_id=self.id)
        self.last_form_img = last_history.form_img_attachment_id.datas if last_history else None

    @api.one
    def _get_last_signature_img(self):
        last_history = self.env['partner.rank.history'].get_last_history(partner_vip_id=self.id)
        self.last_signature_img = last_history.signature_img_attachment_id.datas if last_history else None

    @api.one
    def _get_status_note(self):
        self._cr.execute(QUERY_GET_STATE_NOTE, (self.id,))
        res = self._cr.dictfetchone()
        state = res['state'] if res else ''
        self.status_note = NOTE_DATA.get(state)

    @api.one
    def _get_user_code(self):
        self.user_code = self.get_user_code()

    name = fields.Char(string='Name')
    partner_code = fields.Char(string='Partner code', related='partner_id.x_partner_code')
    partner_old_code = fields.Char(string='Partner old code', related='partner_id.x_partner_old_code', readonly=True)
    team_code = fields.Char(string='Team code', related='partner_id.team_id.x_code', readonly=True)
    user_code = fields.Char(string='User code', compute=_get_user_code, readonly=True)
    phone = fields.Char(string='Phone', related='partner_id.phone', readonly=True)
    email = fields.Char(string='Email', related='partner_id.email', readonly=True)
    birthday = fields.Date(string='Birthday', related='partner_id.x_birthday', readonly=True)
    address = fields.Char(string='Address', related='partner_id.street', readonly=True)
    street2 = fields.Char(string='Street 2', related='partner_id.street2', readonly=True)
    zip = fields.Char(string='Zip', related='partner_id.zip', readonly=True)
    city = fields.Many2one(string='City', related='partner_id.state_id', readonly=True)
    last_profile_img = fields.Binary(string='Profile picture', compute=_get_last_profile_img)
    last_form_img = fields.Binary(string='Form', compute=_get_last_form_img)
    last_signature_img = fields.Binary(string='Signature', compute=_get_last_signature_img)
    next_day_scan = fields.Date(string='Next day scan')
    credit = fields.Float(string='Credit', compute=_calc_total_residual)
    up_rank_date = fields.Date(compute=_get_up_rank_date, string='Up rank date')
    up_rank_expired_date = fields.Date(compute=_get_up_rank_expired_date, string='Up rank expire date')
    status_note = fields.Text(compute=_get_status_note, string='Status Note')
    state = fields.Selection(selection=SELECTION, default='active', compute=_get_state_vip, store=True, string='State')
    customer_rank = fields.Many2one('crm.customer.rank', string='Rank', related='partner_id.x_rank_id', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer', '=', True)], required=True)
    history_ids = fields.One2many('partner.rank.history', 'partner_vip_id', string='Up rank history',
                                  domain=[('state', '!=', 'auto')])
    history_extend_ids = fields.One2many('partner.rank.history.extend', 'partner_vip_id', string='Extend history')

    confirm_ids = fields.One2many('partner.rank.confirm', 'partner_vip_id', string='Confirms')
    company_id = fields.Many2one('res.company', string="Company", related='partner_id.company_id', store=True)
    partner_revenue_ids = fields.One2many('res.partner.revenue', 'partner_vip_id', string='Partner revenue',
                                          related='partner_id.partner_revenue_ids', readonly=True)

    _sql_constraints = [
        ('partner_id_unique', 'unique(partner_id)', 'Khách hàng đã là khách hàng VIP!')
    ]

    @api.model
    def create(self, vals):
        if 'partner_id' in vals:
            partner_name = self.env['res.partner'].browse(vals['partner_id']).name
            vals.update({'name': 'VIP_' + partner_name})
        return super(ResPartnerVip, self).create(vals)

    @api.multi
    def action_up_rank(self):
        ctx = self._context.copy()
        ctx.update({'partner_vip_id': self.id,
                    'exception_from_auto': 0})
        return {
            'name': 'Partner up rank',
            'type': 'ir.actions.act_window',
            'res_model': 'partner.up.rank',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.user_code = self.get_user_code()

    def get_user_code(self):
        if self.partner_id and self.partner_id.user_id:
            employee = self.env['hr.employee'].search([('user_id', '=', self.partner_id.user_id.id)], limit=1)
            if employee:
                return employee.x_employee_code
        return ''
