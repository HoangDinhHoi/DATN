# -*- coding: utf-8 -*-
__author__ = "HoiHD"

from odoo import api, fields, models

STATE_SELECTOR = [('free', 'Free'), ('busy', 'Busy')]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.one
    def _get_state(self):
        time_from = self._context.get('time_from')
        time_to = self._context.get('time_to')
        if not time_from and not time_to:
            self.state = 'free'
            return
        time_from = time_to if not time_from else time_from
        time_to = time_from if not time_to else time_to
        self.state = self.get_employee_state(self.id, time_from, time_to)

    state = fields.Selection(STATE_SELECTOR, string='State', compute=_get_state)

    def get_employee_state(self, employee_id, time_from, time_to, except_booking_id=None):
        query = '''
            SELECT sb.id FROM service_booking sb
            INNER JOIN hr_employee_service_booking_rel hebr ON sb.id = hebr.service_booking_id
            WHERE hebr.hr_employee_id = %s and sb.state != 'cancel' 
                AND ((sb.time_from >= %s AND sb.time_from <= %s) 
                OR (sb.time_to >= %s AND sb.time_to <= %s) 
                OR (sb.time_from <= %s AND sb.time_to >= %s))
        '''
        query_params = [employee_id, time_from, time_to, time_from, time_to, time_from, time_to]
        if except_booking_id:
            query += ''' AND sb.id != %s'''
            query_params += [except_booking_id]
        self._cr.execute(query, tuple(query_params))
        row = self._cr.dictfetchone()
        if row:
            return 'busy'
        return 'free'


