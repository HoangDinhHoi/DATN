# -*- coding: utf-8 -*-
from odoo import models, fields, tools, api

SELECTION = [('pending', 'Pending'), ('suspend', 'Suspend'), ('done', 'Done'), ('deny', 'Denied'), ('auto', 'Auto')]


class PartnerRankHistory(models.Model):
    _name = 'partner.rank.history'
    _description = 'Partner rank history'
    _order = 'create_date ASC'

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

    up_rank_date = fields.Date(string='Up rank date')
    up_rank_expired_date = fields.Date(string='Up rank expired date')
    extend_date = fields.Date(string='Extend Date')
    date_confirm = fields.Datetime(string='Date confirm', help='Ngày xác nhận lên hạng, hoặc ngày xác nhận gia hạn')
    state = fields.Selection(SELECTION, string='State', default='auto')

    from_rank = fields.Many2one('crm.customer.rank', string='From rank')
    to_rank = fields.Many2one('crm.customer.rank', string='To rank')
    partner_vip_id = fields.Many2one('res.partner.vip', string='Partner VIP')
    partner_id = fields.Many2one(related='partner_vip_id.partner_id', string='Partner', store=True)
    request_shop_id = fields.Many2one('crm.team', string='Request Shop')

    form_img_name = fields.Char(string='Form image name')
    form_img_view = fields.Binary(string='Form', inverse=set_image_form, compute=get_image_form)
    form_img_attachment_id = fields.Many2one('ir.attachment', string='Form attachment')

    signature_img_name = fields.Char(string="Signature image name")
    signature_img_view = fields.Binary(string="Signature", inverse=set_image_signature, compute=get_image_signature)
    signature_img_attachment_id = fields.Many2one('ir.attachment', string='Signature attachment')

    profile_img_name = fields.Char(string="Profile image name")
    profile_img_view = fields.Binary(string="Profile", inverse=set_image_profile, compute=get_image_profile)
    profile_img_attachment_id = fields.Many2one('ir.attachment', string='Profile attachment')

    def get_last_history(self, partner_id=False, partner_vip_id=False):
        if not (partner_id or partner_vip_id):
            return False
        domain = [('state', 'in', ('done', 'suspend'))]
        if partner_id:
            domain += [('partner_id', '=', partner_id)]
        if partner_vip_id:
            domain += [('partner_vip_id', '=', partner_vip_id)]
        last_history = self.search(domain, order='create_date DESC', limit=1)
        return last_history if last_history else False
