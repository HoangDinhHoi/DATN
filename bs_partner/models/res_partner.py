# -*- coding: utf-8 -*-
# __author__ = "HoiHD"

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    x_partner_code = fields.Char(string="Mã khách hàng")

    _sql_constraints = [
        ("partner_code_unq", "unique(x_partner_code)", "Mã khách hàng phải duy nhất!")
    ]

    @api.model
    def create(self, vals):
        if vals.get("x_partner_code", "") == "":
            vals['x_partner_code'] = self.env['ir.sequence'].next_by_code("partner_code")
        return super(ResPartner, self).create(vals)
