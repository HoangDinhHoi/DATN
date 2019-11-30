# -*- coding: utf-8 -*-
from datetime import date
import logging

from odoo import api

_logger = logging.getLogger(__name__)


def get_sequence(cr, uid, code):
    env = api.Environment(cr, uid, {})
    ir_sequence = env['ir.sequence']
    sequence_name = code
    sequence_value = ir_sequence.get(sequence_name)
    if not sequence_value:
        args = {
            'name': sequence_name,
            'code': sequence_name,
            'implementation': 'no_gap',
            'padding': 4,
        }
        ir_sequence.create(args)
        sequence_value = ir_sequence.get(sequence_name)
    return sequence_name + sequence_value
