# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

STATE_SELECTOR = [('free', 'Free'), ('busy', 'Busy')]


class CrmTeamBed(models.Model):
    _name = 'crm.team.bed'
    _description = 'Crm team bed'
    _order = 'name ASC'

    @api.one
    def _get_state(self):
        time_from = self._context.get('time_from')
        time_to = self._context.get('time_to')
        if not time_from and not time_to:
            self.state = 'free'
            return
        time_from = time_to if not time_from else time_from
        time_to = time_from if not time_to else time_to
        self.state = self.get_bed_state(self.id, time_from, time_to)

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    team_id = fields.Many2one('crm.team', string='Team', required=True)
    company_id = fields.Many2one('res.company', string='Company', related='team_id.company_id', store=True)
    state = fields.Selection(STATE_SELECTOR, string='State', compute=_get_state)

    @api.model
    def create(self, vals):
        if not vals.get('code', ''):
            vals['code'] = self.__get_bed_code(vals.get('team_id'))
        return super(CrmTeamBed, self).create(vals)

    def get_bed_state(self, bed_id, time_from, time_to, except_booking_id=None):
        query = '''SELECT sb.id FROM service_booking sb
                    INNER JOIN crm_team_bed_service_booking_rel ctbr ON sb.id = ctbr.service_booking_id
                    WHERE ctbr.crm_team_bed_id = %s and sb.state != 'cancel' 
                    AND ((sb.time_from >= %s AND sb.time_from <= %s) 
                        OR (sb.time_to >= %s AND sb.time_to <= %s) 
                        OR (sb.time_from <= %s AND sb.time_to >= %s))'''
        query_params = [bed_id, time_from, time_to, time_from, time_to, time_from, time_to]
        if except_booking_id:
            query += ''' AND sb.id != %s'''
            query_params += [except_booking_id]
        self._cr.execute(query, tuple(query_params))
        row = self._cr.dictfetchone()
        if row:
            return 'busy'
        return 'free'

    def __get_bed_code(self, team_id):
        team = self.env['crm.team'].browse(team_id)
        ir_sequence = self.env['ir.sequence'].sudo()
        sequence_name = team.x_code + '_bed_seq'
        sequence_value = ir_sequence.get(sequence_name)
        if not sequence_value:
            args = {
                'name': sequence_name,
                'code': sequence_name,
                'implementation': 'no_gap',
                'padding': 3,
            }
            ir_sequence.create(args)
            sequence_value = ir_sequence.get(sequence_name)

        return 'B{0}{1}'.format(team.x_code, sequence_value)
