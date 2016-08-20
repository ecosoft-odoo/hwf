# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class NpoObi(models.Model):
    _name = 'npo.obi'
    _description = 'Originator to Beneficiary Information'

    name = fields.Char(
        string='Name',
        size=256,
        required=True,
    )
    description = fields.Char(
        string='Description',
        size=256,
        required=False,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "The name of this OBI must be unique !"),
    ]


class NpoProjectCateg(models.Model):
    _name = 'npo.project.categ'
    _description = 'Project Category'

    name = fields.Char(
        string='Name',
        size=256,
        required=True,
    )
    description = fields.Char(
        string='Description',
        size=256,
        required=False,
    )
    project_ids = fields.One2many(
        'npo.project',
        'project_categ_id',
        string='Projects under this Category',
        readonly=False,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    _sql_constraints = [
        ('uniq_name', 'unique(name)',
         "The name of this project category must be unique !"),
    ]


class NpoProject(models.Model):
    _name = 'npo.project'
    _description = 'Project'

    name = fields.Char(
        string='Name',
        size=256,
        required=True,
    )
    description = fields.Char(
        string='Description',
        size=256,
        required=False)
    project_categ_id = fields.Many2one(
        'npo.project.categ',
        string='Project Category',
        default=lambda self: self._context.get('active_id', False),
    )
    project_line_ids = fields.One2many(
        'npo.project.line',
        'project_id',
        string='Project Lines under this project',
        readonly=False,
    )
    start_period_id = fields.Many2one(
        'account.period',
        string='Start Period',
        required=True,
    )
    end_period_id = fields.Many2one(
        'account.period',
        string='End Period',
        required=True,
    )
    date_start = fields.Date(
        related='start_period_id.date_start',
        string='Start date',
        store=True,
        readonly=True,
    )
    date_stop = fields.Date(
        related='end_period_id.date_stop',
        string='End date',
        store=True,
        readonly=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    _sql_constraints = [
        ('uniq_name', 'unique(name, start_period_id)',
         "The project name and period duration must be unique!"),
    ]

    @api.model
    def _estimate_next_period(self):
        project = self
        if not project.start_period_id or not project.end_period_id:
            raise ValidationError(
                _('There is no period duration define for this project'))
        Period = self.env['account.period']
        period_start = project.start_period_id
        period_end = project.end_period_id
        num_periods = \
            Period.search_count([('special', '=', False),
                                 ('date_start', '>=', period_start.date_start),
                                 ('date_stop', '<=', period_end.date_stop)])
        start_period_id = Period.next(project.end_period_id, 1)
        end_period_id = Period.next(project.end_period_id, num_periods)
        if start_period_id and Period.browse(start_period_id).special:
            start_period_id = Period.next(project.end_period_id, 2)
            end_period_id = Period.next(project.end_period_id, num_periods+1)
        return start_period_id, end_period_id

    @api.model
    def copy(self, vals):
        vals.update(name=_("%s (copy)") % (self.name or ''))
        # Set default period to be next period, plus number of period.
        start_period_id, end_period_id = self._estimate_next_period()
        vals.update({'start_period_id': start_period_id,
                     'end_period_id': end_period_id})
        return super(NpoProject,
                     self.with_context(start_period_id=start_period_id,
                                       end_period_id=end_period_id)).copy(vals)

    @api.multi
    def onchange_start_period_id(self, start_period_id):
        v = {}
        Period = self.env['account.period']
        start_period = Period.browse(start_period_id)
        if start_period_id:
            v['end_period_id'] = Period.next(start_period, 11)
        return {'value': v}


class NpoProjectLine(models.Model):
    _name = 'npo.project.line'
    _description = 'Project Line'

    name = fields.Char(
        string='Name',
        size=256,
        required=True,
    )
    description = fields.Char(
        string='Description',
        size=256,
        required=False,
    )
    project_id = fields.Many2one(
        'npo.project',
        string='Project',
    )
    project_categ_id = fields.Many2one(
        'npo.project.categ',
        related='project_id.project_categ_id',
        string='Project Category',
        store=True,
        readonly=True,
    )
    budget_alloc_total = fields.Float(
        string='Total Budget Allocation',
        compute='_compute_sum_total',
        store=True,
        readonly=True,
    )
    budget_used_total = fields.Float(
        string='Total Budget Used',
        compute='_compute_sum_total',
        store=True,
        readonly=True,
    )
    budget_diff_total = fields.Float(
        string='Total Budget Difference',
        compute='_compute_sum_total',
        store=True,
        readonly=True,
    )
    budget_line = fields.One2many(
        'npo.project.line.budget.line',
        'project_line_id',
        string='Budget Lines',
        readonly=False,
    )
    statement_line = fields.One2many(
        'account.bank.statement.line',
        'project_line_id',
        string='Statement Lines',
        readonly=True,
    )
    activity_id = fields.Many2one(
        'npo.activity',
        string='Activity',
        required=True,
    )
    account_id = fields.Many2one(
        'account.account',
        related='activity_id.account_id',
        string='Account',
        store=True,
        readonly=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    start_period_id = fields.Many2one(
        'account.period',
        related='project_id.start_period_id',
        string='Start Period',
        store=True,
        readonly=True,
    )
    end_period_id = fields.Many2one(
        'account.period',
        related='project_id.end_period_id',
        string='End Period',
        store=True,
        readonly=True,
    )
    date_start = fields.Date(
        related='start_period_id.date_start',
        string='Start date',
        store=True,
        readonly=True,
    )
    date_stop = fields.Date(
        related='start_period_id.date_stop',
        string='Stop date',
        store=True,
        readonly=True,
    )
    _sql_constraints = [
        ('uniq_name', 'unique(name, project_id)',
         "The name of this project line must be unique !"),
    ]

    @api.multi
    @api.depends('budget_line',
                 'budget_line.budget_alloc',
                 'budget_line.budget_used',
                 'budget_line.budget_diff',
                 'statement_line.amount',
                 'statement_line.project_line_id',
                 'statement_line.obi_id')
    def _compute_sum_total(self):
        for project_line in self:
            project_line.budget_alloc_total = 0.0
            project_line.budget_used_total = 0.0
            project_line.budget_diff_total = 0.0
            for budget_line in project_line.budget_line:
                project_line.budget_alloc_total += budget_line.budget_alloc
                project_line.budget_used_total += budget_line.budget_used
            project_line.budget_diff_total = (project_line.budget_alloc_total -
                                              project_line.budget_used_total)

    @api.multi
    def write(self, vals):
        if vals is None:
            vals = {}
        start_period_id = vals.get('start_period_id', False)
        end_period_id = vals.get('end_period_id', False)
        if start_period_id and end_period_id:
            for line in self:
                if start_period_id < line.project_id.start_period_id.id or \
                        end_period_id > line.project_id.end_period_id.id:
                    raise ValidationError(
                        _("Project line's period must lies "
                          "between its project's period"))
        return super(NpoProjectLine, self).write(vals)


class NpoProjectLineBudgetLine(models.Model):
    _name = 'npo.project.line.budget.line'
    _description = 'Project Line Budget Line'

    @api.multi
    @api.depends('project_line_id.statement_line',
                 'project_line_id.statement_line.amount',
                 'project_line_id.statement_line.project_line_id',
                 'project_line_id.statement_line.obi_id',
                 'project_line_id.budget_line',
                 'project_line_id.budget_line.budget_alloc')
    def _compute_budget_used(self, cr, uid, ids, name, args, context):
        for line in self:
            line.budget_used = 0.0
            line.budget_diff = 0.0
            cr.execute("""
                select sum(amount) from account_bank_statement_line sl
                inner join account_bank_statement s on s.id = sl.statement_id
                where project_line_id = %s
                and obi_id = %s""", (line.project_line_id.id, line.obi_id.id))
            result = dict(cr.dictfetchone())
            line.budget_used = result['sum'] and - result['sum'] or 0.0
            line.budget_diff = line.budget_alloc - line.budget_used

    project_line_id = fields.Many2one(
        'npo.project.line',
        string='Project Line',
        ondelete="cascade",
    )
    budget_alloc = fields.Float(
        string='Budget Allocation',
    )
    budget_used = fields.Float(
        compute='_compute_budget_used',
        string='Budget Used',
        store=True,
        readonly=True,
    )
    budget_diff = fields.Float(
        compute='_compute_budget_used',
        string='Budget Difference',
        store=True,
        readonly=True,
    )
    obi_id = fields.Many2one(
        'npo.obi',
        string='Donor',
        required=True,
    )
    _sql_constraints = [
        ('uniq_donor', 'unique(obi_id, project_line_id)',
         "Donor must be unique!"),
    ]

    @api.model
    def create(self, vals):
        if vals is None:
            vals = {}
        vals.update({'budget_alloc': False,
                     'end_period_id': self._context.get('end_period_id')})
        return super(NpoProjectLineBudgetLine, self).create(vals)


class NpoActivity(models.Model):
    _name = 'npo.activity'
    _description = 'Activity'

    name = fields.Char(
        string='Name',
        size=256,
        required=True,
    )
    account_id = fields.Many2one(
        'account.account',
        string='Account',
        required=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "The name of this OBI must be unique !"),
    ]
