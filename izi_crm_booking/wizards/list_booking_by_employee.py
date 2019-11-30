# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class ListBookingByEmployee(models.TransientModel):
    _name = 'list.booking.by.employee'

    name = fields.Char(string='Booking')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    from_date = fields.Date(string='From date')
    to_date = fields.Date(string='To date')
    team_id = fields.Many2one('crm.team', string='Team')

    @api.multi
    def general_booking(self):
        # Xoá dữ liệu cũ
        self._cr.execute('''delete from list_booking_by_employee_line''')
        if self.from_date > self.to_date:
            raise except_orm(_('Thông báo'), _('Bạn đang chọn điều kiện ngày không đúng.'))
        team_id = 0
        if self.team_id:
            team_id = self.team_id.id
        employee_id = 0
        if self.employee_id:
            employee_id = self.employee_id.id

        obj_line = self.env['list.booking.by.employee.line']

        sql = '''SELECT a.name booking, c.id employee_id, a.team_id, a.time_from, a.time_to, a."time"
                FROM service_booking A
                LEFT JOIN hr_employee_service_booking_rel b ON A . ID = b.service_booking_id
                LEFT JOIN hr_employee C ON C . ID = b.hr_employee_id
                WHERE a.time_from::DATE >= %s
                    and a.time_from::DATE <= %s
                    and (a.team_id = %s or %s = 0)
                    and (c.id = %s or %s = 0)'''
        self._cr.execute(sql, (self.from_date,self.to_date,team_id, team_id, employee_id,employee_id))
        lists = self._cr.dictfetchall()

        if len(lists) >= 1:
            for i in lists:
                obj_line.create({
                    'name': i['booking'] and i['booking'] or False,
                    'employee_id': i['employee_id'] and int(i['employee_id']) or False,
                    'team_id': i['team_id'] and i['team_id'] or False,
                    'time_from': i['time_from'] and i['time_from'] or False,
                    'time_to': i['time_to'] and i['time_to'] or False,
                    'time': i['time'] and float(i['time']) or False,
                })
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'gantt',
            'name': _('List Booking'),
            'res_id': False,
            'res_model': 'list.booking.by.employee.line',
            'views': [(self.env.ref('izi_crm_booking.list_booking_by_employee_line_view_gantt').id, 'gantt')],
            'context':{
                'group_by_default_employee': 1,
                'search_default_to_day': 1,
                'short_name': 1,
            }

        }
        return action


class ListBookingByEmployeeList(models.TransientModel):
    _name = 'list.booking.by.employee.line'

    name = fields.Char(string='Name')
    employee_id = fields.Many2one('hr.employee','Employee')
    team_id = fields.Many2one('crm.team', 'Team')
    time_from = fields.Datetime(string="Time From")
    time_to = fields.Datetime(string="Time To")
    time = fields.Float(string='Time', store=True, digits=(16, 2))
