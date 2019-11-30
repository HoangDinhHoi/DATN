# -*- coding: utf-8 -*-
from calendar import monthrange

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, tools
from odoo.exceptions import except_orm


class PartnerUpRank(models.TransientModel):
    _name = 'partner.up.rank'
    _description = 'Partner up rank'

    def _check_is_extend(self):
        for r in self:
            r.is_extend = True if r.to_rank.id == r.partner_id.x_rank_id.id else False

    @api.one
    @api.depends('partner_id')
    def _get_user_code(self):
        self.user_code = ''
        if self.partner_id and self.partner_id.user_id and self.partner_id.user_id.employee_ids:
            self.user_code = self.partner_id.user_id.employee_ids[0].x_employee_code

    name = fields.Char(string='Name', related='partner_id.display_name', default='VIP Customer', store=True)
    partner_vip_id = fields.Many2one('res.partner.vip', string='Partner vip', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    partner_code = fields.Char(string='Partner code', related='partner_id.x_partner_code', readonly=True)
    partner_old_code = fields.Char(string='Partner old code', related='partner_id.x_partner_old_code', readonly=True)
    team_code = fields.Char(string='Team code', related='partner_id.team_id.x_code', readonly=True)
    user_code = fields.Char(string='User code', compute=_get_user_code, readonly=True)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    zip = fields.Char(string='Zip', size=24)
    city = fields.Char(string='City')
    birthday = fields.Date(stirng='Birthday')
    month_rank = fields.Integer(string='Month of rank', store=True)
    note = fields.Text(string='Note')
    is_extend = fields.Boolean(string='Extend rank', compute=_check_is_extend, default=False)
    make_exception = fields.Boolean(string='Extend exception', default=False)
    year_extend = fields.Integer(string='Year extend', default=0)
    register_date = fields.Date(string='Register date', required=True, default=fields.Date.today(), store=True)
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')
    customer_rank = fields.Many2one('crm.customer.rank', string='Rank', related='partner_id.x_rank_id', readonly=True)
    to_rank = fields.Many2one('crm.customer.rank', string='To rank', required=True)

    profile_img_name = fields.Char(string="Profile image name")
    profile_img_view = fields.Binary(string='Profile image')

    is_get_old_form = fields.Boolean(string='Get old form', default=False)
    form_img_name = fields.Char(string='Form image name')
    form_img_view = fields.Binary(string='Form')

    is_get_old_signature = fields.Boolean(string='Get old signature', default=False)
    signature_img_name = fields.Char(string='Signature image name')
    signature_img_view = fields.Binary(string='Signature')

    @api.onchange('to_rank')
    def _onchange_to_rank(self):
        if self.to_rank:
            if self.to_rank.level != self.partner_id.x_rank_id.level:
                self.is_extend = False
                self.month_rank = self.to_rank.active_month
            else:
                self.is_extend = True
                RankRule = self.env['crm.customer.rank.rule']
                rule = RankRule.search([('type', '=', 'extend'),
                                        ('brand_id', '=', self.partner_id.brand_id.id),
                                        ('rank_id', '=', self.to_rank.id)], limit=1)
                if rule:
                    data_extend = rule.get_year_extend_and_revenue(self.partner_id.id, self.register_date)
                    year = data_extend['year']
                    if year and year > 0:
                        self.month_rank = year * 12
                    else:
                        self.month_rank = 0

    @api.onchange('register_date')
    def _onchange_register_date(self):
        if self.register_date > fields.Date.today():
            self.register_date = fields.Date.today()
            return {
                'warning': {
                    'title': 'Thông báo',
                    'message': 'Bạn không thể chọn ngày trong tương lai'}
            }

    @api.model
    def default_get(self, fields):
        res = super(PartnerUpRank, self).default_get(fields)
        partner_vip = self.env['res.partner.vip'].search([('id', '=', self._context.get('partner_vip_id', None))])
        if not partner_vip:
            return res
        if 'partner_id' in fields:
            res.update({'partner_id': partner_vip.partner_id.id})
        if 'phone' in fields:
            res.update({'phone': partner_vip.partner_id.phone})
        if 'email' in fields:
            res.update({'email': partner_vip.partner_id.email})
        if 'street' in fields:
            res.update({'street': partner_vip.partner_id.street})
        if 'street2' in fields:
            res.update({'street2': partner_vip.partner_id.street2})
        if 'zip' in fields:
            res.update({'zip': partner_vip.partner_id.zip})
        if 'city' in fields:
            res.update({'city': partner_vip.partner_id.city})
        if 'state_id' in fields:
            res.update({'state_id': partner_vip.partner_id.state_id.id})
        if 'country_id' in fields:
            res.update({'country_id': partner_vip.partner_id.country_id.id})
        if 'birthday' in fields:
            res.update({'birthday': partner_vip.partner_id.x_birthday})
        return res

    def action_up_rank(self):
        self.prepare_up_rank()
        if self.customer_rank.level == self.to_rank.level and self.to_rank.code == '1PRE':
            self.extend_rank()
        else:
            self.up_rank()

    def prepare_up_rank(self):
        confirm_exist = self.env['partner.rank.confirm'].search([('partner_id', '=', self.partner_id.id),
                                                                 ('state', 'not in', ['done', 'cancel', 'nothing'])])
        if confirm_exist:
            raise except_orm("Lỗi", "Khách hàng này đang có một yêu cầu lên hạng đang chờ phê duyệt")
        if self.customer_rank.level > self.to_rank.level:
            raise except_orm("Thông báo", "Bạn phải chọn hạng cao hơn hạng hiện tại của khách hàng")
        if self.customer_rank.level == self.to_rank.level and self.to_rank.code != '1PRE':
            raise except_orm("Thông báo", "Không thể gia hạn cho khách hàng không phải Premier")

    def extend_rank(self):
        if self.month_rank == 0 and self.year_extend == 0:
            raise except_orm("Thông báo", "Hãy nhập số năm gia hạn > 0")
        type_extend = 'extend_exception'
        if self.month_rank != 0:
            type_extend = 'extend'
            if self.make_exception:
                if (self.year_extend * 12) <= self.month_rank:
                    raise except_orm("Thông báo", "Số năm gia hạn ngoại lệ phải lớn hơn số năm khách hàng được gia hạn")
                type_extend = 'extend_exception'
        partner_vip_id = self._context.get('partner_vip_id', None)
        if not partner_vip_id:
            raise except_orm('Lỗi', 'Không tồn tại khách hàng VIP')
        last_history = self.env['partner.rank.history'].get_last_history(partner_vip_id=partner_vip_id)
        if not last_history:
            raise except_orm("Lỗi", "Không thể gia hạn cho KH chưa có lịch sử lên hạng")
        month_rank = self.month_rank
        if type_extend != 'extend':
            month_rank = self.year_extend * 12
        self.create_confirm(month_rank, partner_vip_id, type_extend, last_history)

    def up_rank(self):
        PartnerRankHistory = self.env['partner.rank.history']
        partner_vip_id = self._context.get('partner_vip_id', None)
        if not partner_vip_id:
            return
        partner_vip = self.env['res.partner.vip'].browse(partner_vip_id)
        old_rank_id = partner_vip.partner_id.x_rank_id.id
        up_rank_expired_date = self.register_date + relativedelta(months=+self.month_rank)
        last_date = monthrange(up_rank_expired_date.year, up_rank_expired_date.month)[1]
        up_rank_expired_date = up_rank_expired_date.strftime('%Y-%m') + '-' + str(last_date)
        history_suspend = PartnerRankHistory.search([('partner_vip_id', '=', partner_vip_id),
                                                     ('state', '=', 'suspend')])
        if history_suspend:
            raise except_orm("Lỗi",
                             "Khách hàng này đang có một yêu cầu lên hạng đang treo và chờ phê duyệt")
        history_state = 'pending'
        confirm_type = 'exception'
        history = PartnerRankHistory.create({
            'from_rank': old_rank_id,
            'to_rank': self.to_rank.id,
            'up_rank_date': self.register_date,
            'up_rank_expired_date': up_rank_expired_date,
            'partner_vip_id': partner_vip_id,
            'state': history_state
        })
        self.create_confirm(self.month_rank, partner_vip_id, confirm_type, history)

    def create_confirm(self, month_rank, partner_vip_id, type, history):
        last_history = self.env['partner.rank.history'].get_last_history(partner_vip_id=partner_vip_id)
        profile_img_attachment_id = self.get_attachment_id('profile_img', self.profile_img_name, self.profile_img_view)
        form_img_attachment_id = last_history.form_img_attachment_id.id if self.is_get_old_form \
            else self.get_attachment_id('form_img', self.form_img_name, self.form_img_view)
        signature_img_attachment_id = last_history.signature_img_attachment_id.id if self.is_get_old_signature \
            else self.get_attachment_id('signature_img', self.signature_img_name, self.signature_img_view)

        return self.env['partner.rank.confirm'].create({
            'partner_id': self.partner_id.id,
            'phone': self.phone,
            'email': self.email,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'state_id': self.state_id.id,
            'country_id': self.country_id.id,
            'to_rank': self.to_rank.id,
            'register_date': self.register_date,
            'month_rank': month_rank,
            'birthday': self.birthday,
            'partner_vip_id': partner_vip_id,
            'profile_img_attachment_id': profile_img_attachment_id,
            'is_get_old_form': self.is_get_old_form,
            'form_img_attachment_id': form_img_attachment_id,
            'is_get_old_signature': self.is_get_old_signature,
            'signature_img_attachment_id': signature_img_attachment_id,
            'state': 'new',
            'note': self.note,
            'user_id': self._uid,
            'shop_confirm_time': fields.Datetime.now(),
            'type': type,
            'history_id': history.id,
        })

    @api.onchange('is_get_old_signature')
    def onchange_is_get_old_signature(self):
        if self.is_get_old_signature:
            return self.get_old_signature_partner_customer()
        self.signature_img_view = False

    def get_old_signature_partner_customer(self):
        partner_vip_id = self._context.get('partner_vip_id')
        last_history = self.env['partner.rank.history'].get_last_history(partner_vip_id=partner_vip_id)
        if not last_history:
            return
        if last_history.signature_img_attachment_id:
            self.signature_img_name = last_history.signature_img_attachment_id.datas_fname
            self.signature_img_view = last_history.signature_img_attachment_id.datas
            return
        self.is_get_old_signature = False
        return {
            'warning': {
                'title': 'Thông báo',
                'message': 'Khách hàng này chưa tồn tại chữ ký nào trên hệ thống.'}
        }

    @api.onchange('is_get_old_form')
    def onchange_is_get_old_form(self):
        if self.is_get_old_form:
            return self.get_old_form_partner_customer()
        self.form_img_view = False

    def get_old_form_partner_customer(self):
        partner_vip_id = self._context.get('partner_vip_id')
        last_history = self.env['partner.rank.history'].get_last_history(partner_vip_id=partner_vip_id)
        if not last_history:
            return
        if last_history.form_img_attachment_id:
            self.form_img_name = last_history.form_img_attachment_id.datas_fname
            self.form_img_view = last_history.form_img_attachment_id.datas
            return
        self.is_get_old_form = False
        return {
            'warning': {
                'title': 'Thông báo',
                'message': 'Khách hàng này chưa tồn tại biểu mẫu nào trên hệ thống.'}
        }

    def get_attachment_id(self, name, fname, data):
        images = self.resize_image(data)
        res = self.env['ir.attachment'].create({'name': name,
                                                'datas_fname': fname,
                                                'datas': images['image_medium']})
        return res.id

    @staticmethod
    def resize_image(data):
        return tools.image_get_resized_images(data, avoid_resize_medium=True, sizes={'image_medium': (300, 300)})
