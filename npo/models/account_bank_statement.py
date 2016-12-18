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

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    conversion_rate = fields.Float(
        string='Conversion Rate (€)',
        compute='_compute_conversion_rate',
        digits_compute=dp.get_precision('Account'),
    )
    line_cashin_ids = fields.One2many(
        'account.bank.statement.line',
        'statement_id',
        string='Statement lines',
        domain=[('cash_type', '=', 'cashin')],
        states={'confirm': [('readonly', True)]},
    )
    line_cashout_ids = fields.One2many(
        'account.bank.statement.line',
        'statement_id',
        string='Statement lines',
        domain=[('cash_type', '=', 'cashout')],
        states={'confirm': [('readonly', True)]},
    )
    date_start = fields.Date(
        string='Period Date Start',
        related='period_id.date_start',
    )
    date_stop = fields.Date(
        string='Period Date Stop',
        related='period_id.date_stop',
    )

    @api.multi
    @api.depends()
    def _compute_conversion_rate(self):

        self._cr.execute("select id from res_currency where name = 'EUR';")
        res = self._cr.dictfetchone()
        EUR = res['id'] or False

        self._cr.execute("select id from res_currency where name = 'THB';")
        res = self._cr.dictfetchone()
        THB = res['id'] or False

        for obj in self:
            euro = self.env['res.currency'].browse(EUR)  # EUR
            thai = self.env['res.currency'].browse(THB)  # THAI
            c = self._context.copy()
            c.update({'date': obj.date})
            rate = self.env['res.currency'].\
                with_context(c)._get_conversion_rate(euro, thai)
            obj.conversion_rate = rate

    @api.model
    def _prepare_move_line_vals(self, st_line, move_id, debit, credit,
                                currency_id=False, amount_currency=False,
                                account_id=False, partner_id=False):
        res = super(AccountBankStatement, self).\
            _prepare_move_line_vals(st_line, move_id, debit, credit,
                                    currency_id=currency_id,
                                    amount_currency=amount_currency,
                                    account_id=account_id,
                                    partner_id=partner_id)
        res.update({'doc_number': st_line.doc_number,
                    'description': st_line.description,
                    'activity_id': st_line.activity_id.id,
                    'project_line_id': st_line.project_line_id.id,
                    'project_id': st_line.project_id.id,
                    'project_categ_id': st_line.project_categ_id.id,
                    'obi_id': st_line.obi_id.id,
                    'obi_dest_id': st_line.obi_dest_id.id,
                    })
        return res


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'
    _order = 'id desc'

    name = fields.Char(
        string='OBI',
        required=False,
        help="Originator to Beneficiary Information"
    )
    cash_type = fields.Selection(
        [('cashin', 'In'),
         ('cashout', 'Out')],
        string='In/Out',
    )
    obi_id = fields.Many2one(
        'npo.obi',
        string='Donor',
        required=False,
    )
    obi_dest_id = fields.Many2one(
        'npo.obi',
        string='Rpt Donor',
        required=False
    )
    doc_number = fields.Char(
        string='Ref#',
        required=False,
    )
    project_categ_id = fields.Many2one(
        'npo.project.categ',
        related='project_id.project_categ_id',
        string='Project Categ',
        store=True,
        readonly=True,
    )
    project_id = fields.Many2one(
        'npo.project',
        string='Project',
        required=False,
    )
    project_line_id = fields.Many2one(
        'npo.project.line',
        string='Line',
        required=False,
        domain="[('project_id', '=', project_id)]",
    )
    activity_id = fields.Many2one(
        'npo.activity',
        string='Activity',
        domain="[('project_line_ids', 'in', project_line_id)]",
    )
    description = fields.Char(
        string='Description',
        size=256,
        required=False,
    )
    purpose = fields.Char(
        string='Purpose',
        size=256,
    )
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
    )
    unit_price = fields.Float(
        string='Unit Price',
        default=0.0,
    )

    @api.onchange('project_id')
    def _onchange_project_id(self):
        self.project_line_id = False

    @api.onchange('project_line_id')
    def _onchange_project_line_id(self):
        obi_ids = [x.obi_id.id for x in self.project_line_id.budget_line]
        self.obi_id = obi_ids and obi_ids[0] or False
        self.account_id = self.project_line_id.account_id
        return {'domain': {'obi_id': [('id', 'in', obi_ids)]}}

    @api.onchange('obi_id', 'description')
    def _onchange_obi_id(self):
        if not self.obi_id:
            self.name = self.description
        else:
            self.name = self.obi_id.name

    @api.onchange('quantity', 'unit_price')
    def _onchange_qty_price(self):
        self.amount = (self.quantity *
                       self.unit_price *
                       (self.cash_type == 'cashin' and 1 or -1))

    @api.model
    def create(self, vals):
        if vals.get('cash_type', False):
            if vals.get('cash_type', 'cashin') == 'cashout':
                vals['amount'] = - abs(vals['amount'])  # Always keep negative
            else:
                vals['amount'] = abs(vals['amount'])  # Always keep as positive
        return super(AccountBankStatementLine, self).create(vals)

    @api.multi
    def write(self, vals):
        line = self[0]
        if line and line.cash_type:
            if vals.get('amount', False):
                if line.cash_type == 'cashout':
                    vals['amount'] = - abs(vals['amount'])
                if line.cash_type == 'cashin':
                    vals['amount'] = abs(vals['amount'])
            return super(AccountBankStatementLine, line).write(vals)
        return super(AccountBankStatementLine, self).write(vals)
