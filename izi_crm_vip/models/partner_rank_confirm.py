# -*- coding: utf-8 -*-
from calendar import monthrange

from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo import models, fields, api, tools
from odoo.exceptions import except_orm

SELECTION_TYPE = [('auto', 'Automatic'), ('auto_extend', 'Automatic extend'), ('auto_suspend', 'Suspending'),
                  ('normal', 'Normal'), ('suspend', 'Suspending'), ('exception', 'Exception'), ('extend', 'Extend'),
                  ('extend_exception', 'Extend exception')]
SELECTION_STATE = [('auto', 'Auto suggest'), ('new', 'New'), ('approve', 'Pending Approve'), ('done', 'Done'),
                   ('cancel', 'Canceled'), ('nothing', 'Do nothing')]
DF = '%Y-%m-%d'


class PartnerRankConfirm(models.Model):
    _name = 'partner.rank.confirm'
    _description = 'Partner rank confirm'
    _order = 'register_date DESC, create_date DESC'

    @api.one
    def get_user_code(self):
        if self.partner_id and self.partner_id.user_id and self.partner_id.user_id.employee_ids:
            return self.partner_id.user_id.employee_ids[0].x_employee_code
        return ''

    @api.one
    def set_image_form(self):
        if not self.form_img_view:
            self.form_img_attachment_id.unlink()
            return
        if not self.form_img_attachment_id:
            obj = self.env['ir.attachment'].create({'name': 'form_img_view'})
            self.write({'form_img_attachment_id': obj.id})
        images = self.resize_image(self.form_img_view)
        self.form_img_attachment_id.write({'datas_fname': self.form_img_name,
                                           'datas': images['image_medium']})

    @api.one
    def get_image_form(self):
        if self.form_img_attachment_id:
            self.form_img_name = self.form_img_attachment_id.datas_fname
            self.form_img_view = self.form_img_attachment_id.datas
        else:
            self.form_img_name = ''
            self.form_img_view = None

    @api.one
    def set_image_signature(self):
        if not self.signature_img_view:
            self.signature_img_attachment_id.unlink()
            return
        if not self.signature_img_attachment_id:
            obj = self.env['ir.attachment'].create({'name': 'signature_img_view'})
            self.write({'signature_img_attachment_id': obj.id})
        images = self.resize_image(self.signature_img_view)
        self.signature_img_attachment_id.write({'datas_fname': self.signature_img_name,
                                                'datas': images['image_medium']})

    @api.one
    def get_image_signature(self):
        if self.signature_img_attachment_id:
            self.signature_img_name = self.signature_img_attachment_id.datas_fname
            self.signature_img_view = self.signature_img_attachment_id.datas
        else:
            self.signature_img_name = ''
            self.signature_img_view = None

    @api.one
    def set_image_profile(self):
        if not self.profile_img_view:
            self.profile_img_attachment_id.unlink()
            return
        if not self.profile_img_attachment_id:
            obj = self.env['ir.attachment'].create({'name': 'profile_img_view'})
            self.write({'profile_img_attachment_id': obj.id})
        images = self.resize_image(self.profile_img_view)
        self.profile_img_attachment_id.write({'datas_fname': self.profile_img_name,
                                              'datas': images['image_medium']})

    @api.one
    def get_image_profile(self):
        if self.profile_img_attachment_id:
            self.profile_img_name = self.profile_img_attachment_id.datas_fname
            self.profile_img_view = self.profile_img_attachment_id.datas
        else:
            self.profile_img_name = ''
            self.profile_img_view = None

    @staticmethod
    def resize_image(data):
        return tools.image_get_resized_images(data, avoid_resize_medium=True, sizes={'image_medium': (300, 300)})

    name = fields.Char(string='Name', default='Customer rank confirm')
    partner_vip_id = fields.Many2one('res.partner.vip', string='Partner VIP Ref')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    customer_rank = fields.Many2one('crm.customer.rank', string='Rank', related='partner_id.x_rank_id', readony=True)
    partner_code = fields.Char(related='partner_id.x_partner_code', readonly=True)
    partner_old_code = fields.Char(related='partner_id.x_partner_old_code', readonly=True)
    team_code = fields.Char(related='partner_id.team_id.x_code', readonly=True, string='Team code')
    user_code = fields.Char(compute=get_user_code, string='User code')
    type = fields.Selection(SELECTION_TYPE, string='Type', default='normal')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    zip = fields.Char(string='Zip', size=24)
    city = fields.Char(string='City')
    birthday = fields.Date(stirng='Birthday')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')
    note = fields.Text(string='Note')

    user_id = fields.Many2one('res.users', string='User request')
    to_rank = fields.Many2one('crm.customer.rank', string='To rank')
    register_date = fields.Date(string='Register date')
    confirm_date = fields.Datetime(string='Confirm date', required=True, default=fields.Datetime.now())
    month_rank = fields.Integer(string='Month of rank')

    is_get_old_form = fields.Boolean(string='Get old form', default=False)
    form_img_attachment_id = fields.Many2one('ir.attachment', string='Form attachment')
    form_img_name = fields.Char(string='Form image name')
    form_img_view = fields.Binary(string='Form', inverse=set_image_form, compute=get_image_form)

    is_get_old_signature = fields.Boolean(string='Get old signature', default=False)
    signature_img_attachment_id = fields.Many2one('ir.attachment', string='Signature attachment')
    signature_img_name = fields.Char(string='Signature image name')
    signature_img_view = fields.Binary(string='Signature', inverse=set_image_signature, compute=get_image_signature)

    profile_img_attachment_id = fields.Many2one('ir.attachment', string='Profile attachment')
    profile_img_name = fields.Char(string='Profile image name')
    profile_img_view = fields.Binary(string='Profile image', inverse=set_image_profile, compute=get_image_profile)

    missing_documents = fields.Boolean(string='Missing documents', compute='_get_document', store=True)

    shop_confirm_time = fields.Datetime(string='Shop confirm time')
    crm_confirm_time = fields.Datetime(string='Crm confirm time')
    director_confirm_time = fields.Datetime(string='Director confirm time')

    history_id = fields.Many2one('partner.rank.history', string='History ref')
    old_history_ids = fields.One2many(related='partner_vip_id.history_ids')
    state = fields.Selection(SELECTION_STATE, default='new')
    partner_revenue_ids = fields.One2many('res.partner.revenue', 'partner_vip_id', string='Partner revenue',
                                          related='partner_id.partner_revenue_ids',
                                          readonly=True)

    @api.depends('form_img_view', 'signature_img_view')
    def _get_document(self):
        for r in self:
            r.missing_documents = False if r.form_img_view and r.signature_img_view else True

    @api.multi
    def complete_documents(self):
        if self.missing_documents:
            view = self.env.ref('izi_crm_vip.confirm_edit_img_view')
            ctx = self._context.copy()
            ctx.update({'partner_rank_confirm_id': self.id})
            return {
                'name': 'Detail',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'confirm.edit.img',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
                'context': ctx,
            }

    @api.multi
    def action_confirm(self):
        if self.register_date > fields.Date.today():
            raise except_orm("Lỗi", "Ngày yêu cầu không được lớn hơn ngày hiện tại")
        self.write({'state': 'approve', 'crm_confirm_time': fields.Date.today()})

    @api.multi
    def action_extend(self):
        if self.register_date > fields.Date.today():
            raise except_orm("Lỗi", "Ngày yêu cầu không được lớn hơn ngày hiện tại")
        if self.month_rank == 0:
            raise except_orm('Lỗi', "Khách hàng này chưa đủ doanh số để gia hạn")
        year = self.month_rank // 12
        up_rank_expired_date = self.history_id.up_rank_expired_date + relativedelta(years=year)
        self.history_id.write({
            'up_rank_expired_date': up_rank_expired_date.strftime(DF),
            'extend_date': self.register_date.strftime(DF),
            'form_img_attachment_id': self.form_img_attachment_id.id,
            'signature_img_attachment_id': self.signature_img_attachment_id.id,
            'profile_img_attachment_id': self.profile_img_attachment_id.id,
            'state': 'done'
        })
        self.env['partner.rank.history.extend'].create({
            'rank_id': self.history_id.to_rank.id,
            'extend_date': self.register_date.strftime(DF),
            'year_extend': year,
            'partner_vip_id': self.partner_vip_id.id,
        })
        self.write({'state': 'done', 'crm_confirm_time': fields.Date.today()})
        self.do_update_customer_info()

    @api.multi
    def action_cancel(self):
        if self.history_id.state != 'auto' and self.type not in ['extend', 'auto_extend', 'extend_exception']:
            self.history_id.write({'state': 'deny'})
        if self.type in ['suspend', 'auto_suspend']:
            self.partner_id.write({'x_rank_id': self.history_id.from_rank.id})
        if self.state == 'new':
            self.write({'state': 'cancel', 'crm_confirm_time': fields.Date.today()})
        elif self.state == 'approve':
            self.write({'state': 'cancel', 'director_confirm_time': fields.Date.today()})

    @api.multi
    def action_up_rank(self):
        if not self.register_date:
            raise except_orm("Lỗi", "Bạn cần nhập ngày yêu cầu")
        if self.register_date > fields.Date.today():
            raise except_orm("Lỗi", "Ngày yêu cầu không được lớn hơn ngày hiện tại")
        if self.type not in ['suspend', 'auto_suspend']:
            self.partner_id.write({'x_rank_id': self.to_rank.id})

        next_year = self.register_date + relativedelta(months=+self.month_rank)
        last_date = monthrange(next_year.year, next_year.month)[1]
        up_rank_date = self.register_date
        up_rank_expired_date = str(next_year.year) + '-' + str(next_year.month) + '-' + str(last_date)
        self.history_id.write({
            'up_rank_date': up_rank_date,
            'up_rank_expired_date': up_rank_expired_date,
            'form_img_attachment_id': self.form_img_attachment_id.id,
            'signature_img_attachment_id': self.signature_img_attachment_id.id,
            'profile_img_attachment_id': self.profile_img_attachment_id.id,
            'state': 'done'
        })
        self.do_update_customer_info()
        if self.state == 'new':
            self.write({'state': 'done', 'crm_confirm_time': fields.Datetime.now()})
        elif self.state == 'approve':
            self.write({'state': 'done', 'director_confirm_time': fields.Datetime.now()})

    def do_update_customer_info(self):
        self.partner_id.write({
            'phone': self.phone if self.phone else self.partner_id.phone,
            'email': self.email if self.email else self.partner_id.email,
            'street': self.street if self.street else self.partner_id.street,
            'street2': self.street2 if self.street2 else self.partner_id.street2,
            'zip': self.zip if self.zip else self.partner_id.zip,
            'city': self.city if self.city else self.partner_id.city,
            'state_id': self.state_id.id if self.state_id.id else self.partner_id.state_id.id,
            'country_id': self.country_id.id if self.country_id.id else self.partner_id.country_id.id,
            'x_birthday': self.birthday if self.birthday else self.partner_id.x_birthday,
        })

    @api.onchange('is_get_old_form')
    def onchange_is_get_old_form(self):
        if not self.is_get_old_form:
            self.form_img_view = False
            return
        last_history = self.env['partner.rank.history'].search([('partner_vip_id.partner_id', '=', self.partner_id.id),
                                                                ('state', '=', 'done'),
                                                                ('form_img_attachment_id', '!=', False)],
                                                               order='create_date DESC', limit=1)
        if last_history:
            self.form_img_view = last_history.form_img_attachment_id.datas
            return
        self.is_get_old_form = False
        return {
            'warning': {
                'title': 'Thông báo',
                'message': 'Khách hàng này chưa tồn tại biểu mẫu nào trên hệ thống.'}
        }

    @api.onchange('is_get_old_signature')
    def onchange_is_get_old_signature(self):
        if not self.is_get_old_signature:
            self.signature_img_view = False
            return
        last_history = self.env['partner.rank.history'].search([('partner_vip_id.partner_id', '=', self.partner_id.id),
                                                                ('state', '=', 'done'),
                                                                ('signature_img_attachment_id', '!=', False)],
                                                               order='create_date DESC', limit=1)
        if last_history:
            self.signature_img_view = last_history.signature_img_attachment_id.datas
            return
        self.is_get_old_signature = False
        return {
            'warning': {
                'title': 'Thông báo',
                'message': 'Khách hàng này chưa tồn tại chữ ký nào trên hệ thống.'}
        }

    @api.multi
    def action_get_detail(self):
        view_id = self.env.ref('izi_crm_vip.partner_rank_confirm_form_view').id
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'partner.rank.confirm',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'res_id': self.id,
            'flags': {'action_buttons': False}
        }

    def validate_partner_revenue_to_up_rank(self, brand, customer_id, to_rank):
        def compute_percent_missing_revenue(revenue, redeem_point):
            if revenue == 0:
                return 100
            return (redeem_point - revenue) / revenue * 100
        query_get_revenue = """SELECT sum(revenue) total_revenue 
                                FROM res_partner_revenue 
                                WHERE partner_id = %s and revenue_date >= %s"""
        query_get_rule = """SELECT rank_id, target_revenue 
                            FROM crm_customer_rank_rule 
                            WHERE target_revenue >= %s 
                                AND type = 'up' AND brand_id = %s 
                            ORDER BY target_revenue ASC 
                            LIMIT 1"""
        revenue_date = (datetime.today() - relativedelta(months=12)).strftime('%Y-%m') + '-01'
        self._cr.execute(query_get_revenue, (customer_id, revenue_date, ))
        revenue = self._cr.dictfetchone()
        total_revenue = revenue['total_revenue'] or 0
        self._cr.execute(query_get_rule, (total_revenue, brand, ))
        rule = self._cr.dictfetchone()
        if not rule:
            return True
        rank = rule['rank'] or 0
        target_revenue = rule['target_revenue'] or 0

        to_rank = self.env['customer.rank'].browse(to_rank)
        rank = self.env['customer.rank'].browse(rank)

        user_obj = self.env['res.users']
        is_sir = user_obj.has_group('ev_crm.group_director')
        is_manager = user_obj.has_group('base.group_sale_manager')
        is_lead = user_obj.has_group('base.group_sale_salesman_all_leads')

        if not (self._uid == 1) and not is_sir:
            if is_manager:
                if to_rank.level > rank.level and compute_percent_missing_revenue(total_revenue, target_revenue) > 20:
                    raise except_orm('Cảnh báo', 'Bạn không thể nâng hạng với doanh thu hiện tại của khách hàng')
                return True
            elif is_lead:
                if to_rank.level > rank.level and compute_percent_missing_revenue(total_revenue, target_revenue) > 5:
                    raise except_orm('Cảnh báo', 'Bạn không thể nâng hạng với doanh thu hiện tại của khách hàng')
                return True
            return False
        return True
