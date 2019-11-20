# -*- coding: utf-8 -*-

from odoo import models, fields, api

STATE_BED = [("busy", "Bận"), ("free", "Trống")]


class BookingBed(models.Model):
    _name = "service.bed"
    _description = "Thông tin giường"

    name = fields.Char(string="Tên")
    code = fields.Char(string="Mã")
    state = fields.Selection(STATE_BED, default="free", string="Trạng thái")
    description = fields.Text(string="Mô tả")

    _sql_constraints = [
        ("bed_code_unq", "UNIQUE(code)", "Mã giường phải duy nhất!")
    ]

    @api.model
    def create(self, vals):
        if vals.get("code", "") == "":
            vals['code'] = self.env['ir.sequence'].next_by_code("service.bed.code")
        return super(BookingBed, self).create(vals)

    def get_bed_state(self, bed_id, time_from, time_to, except_booking_id=None):
        query = """
            SELECT *
            FROM service_booking sb
            INNER JOIN service_bed_service_booking_rel sr ON sr.service_booking_id=sb.id
            WHERE sr.service_bed_id=%s AND sb.state != 'cancel'
            AND ((sb.time_from >= %s AND sb.time_from <= %s)
                OR (sb.time_from >= %s AND sb.time_to <= %s)
                OR (sb.time_to >= %s AND sb.time_to <= %s)) 
        """
        query_params = [bed_id, time_from, time_to, time_from, time_to, time_from, time_to]
        if except_booking_id:
            query += ''' AND sb.id != %s'''
            query_params += [except_booking_id]
        self._cr.execute(query, tuple(query_params))
        row = self._cr.dictfetchone()
        if row:
            return 'busy'
        return 'free'

