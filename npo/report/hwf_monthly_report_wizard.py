# -*- coding: utf-8 -*-
from openerp import api, fields, models, _


class HWFMonthlyReportWizard(models.TransientModel):
    _name = 'hwf.monthly.report.wizard'

    project_categ_id = fields.Many2one(
        'npo.project.categ',
        string='Project Category',
    )
    date_from = fields.Date(
        string='Date From',
    )
    date_to = fields.Date(
        string='Date To',
    )

    @api.multi
    def open_report(self):
        self.ensure_one()
        action = self.env.ref('npo.action_hwf_monthly_report_all')
        result = action.read()[0]
        result.update({'domain': [
            ('project_categ_id', '=', self.project_categ_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]})
        return result


