# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools


class ConfirmEditImg(models.TransientModel):
    _name = 'confirm.edit.img'
    _description = 'Confirm edit image'

    form_img_name = fields.Char(string='Form image name')
    form_img_view = fields.Binary(string='Form image')

    signature_img_name = fields.Char(string='Signature image name')
    signature_img_view = fields.Binary(string='Signature image')

    profile_img_name = fields.Char(string="Profile image name")
    profile_img_view = fields.Binary(string="Profile image")

    @api.multi
    def action_confirm(self):
        vals = {}
        if self.form_img_view:
            vals.update({'form_img_attachment_id': self.get_attachment_image_id(self.form_img_name,
                                                                                self.form_img_view)})
        if self.signature_img_view:
            vals.update({'signature_img_attachment_id': self.get_attachment_image_id(self.signature_img_name,
                                                                                     self.signature_img_view)})
        if self.profile_img_view:
            vals.update({'profile_img_attachment_id': self.get_attachment_image_id(self.profile_img_name,
                                                                                   self.profile_img_view)})
        self.rank_confirm_id.history_id.write(vals)
        if self.rank_confirm_id.history_id.form_img_view and self.rank_confirm_id.history_id.signature_img_view:
            self.rank_confirm_id.missing_documents = False

    def get_attachment_image_id(self, fname, data):
        images = tools.image_get_resized_images(data, sizes={'image_medium': (300, 300)}, avoid_resize_medium=True)
        attachment = self.env['ir.attachment'].create({'datas_fname': fname,
                                                       'datas': images['image_medium']})
        return attachment.id
