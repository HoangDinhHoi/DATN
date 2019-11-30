# -*- coding: utf-8 -*-
from odoo import api, fields, models


class IrRule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    def domain_get(self, model_name, mode='read'):
        context = self._context
        if 'force_record_rule' in context and context['force_record_rule'] == 1:
            dom = False
        else:
            dom = self._compute_domain(model_name, mode)
        if dom:
            # _where_calc is called as superuser. This means that rules can
            # involve objects on which the real uid has no acces rights.
            # This means also there is no implicit restriction (e.g. an object
            # references another object the user can't see).
            query = self.env[model_name].sudo()._where_calc(dom, active_test=False)
            return query.where_clause, query.where_clause_params, query.tables
        return [], [], ['"%s"' % self.env[model_name]._table]