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

from openerp.osv import models, fields, api
import openerp.addons.decimal_precision as dp

EUR = 351
THAI = 142


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    conversion_rate = fields.Float(
        string='Conversion Rate (EURO)',
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
        states={'confirm': [('readonly', True)]})

    @api.multi
    @api.depends()
    def _compute_conversion_rate(self):
        res = {}
        for obj in self:
            euro = self.env['res.currency'].browse(EUR)  # EUR
            thai = self.env['res.currency'].browse(THAI)  # THAI
            c = self._context.copy()
            c.update({'date': obj.date})
            rate = self.env['res.currency'].\
                with_context(c)._get_conversion_rate(euro, thai)
            obj.conversion_rate = rate
        return res

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
                    'description': st_line.description})
        return res


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'
    _order = 'id'

    name = fields.Char(
        string='OBI',
        required=False,
        help="Originator to Beneficiary Information"
    )
    cash_type = fields.Selection(
        [('cashin', 'In'),
         ('cashout', 'Out')],
        string='In/Out',
        default=lambda self: self._context.get('default_cashtype'),
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
        string='Project Categ',
        required=False,
    )
    project_id = fields.Many2one(
        'npo.project',
        string='Project',
        domain="[('project_categ_id','=',project_categ_id)]",
        required=False,
    )
    project_line_id = fields.Many2one(
        'npo.project.line',
        string='Line',
        required=False,
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
    quantity = fields.float(
        string='Quantity',
        default=1.0,
    )
    unit_price = fields.float(
        string='Unit Price',
        default=0.0,
    )

    @api.multi
    def onchange_date(self):
        if self._context.get('period_id', False):
            Period = self.env['account.period']
            p = Period.browse(self._context.get('period_id'))
            return {'domain': {
                        'project_line_id': [('date_start', '<=', p.date_start),
                                            ('date_stop', '>=', p.date_stop)]
                        }
                    }

    @api.multi
    def onchange_project_line_id(self, project_line_id, account_id):
        if not project_line_id and not account_id:
            return {}
        obj = self.env['npo.project.line']
        # Case 1: If choose project_line, assign account and other info.
        if project_line_id and not account_id:
            project_line = obj.browse(project_line_id)
            account = project_line.account_id
            project = project_line.project_id
            categ = project_line.project_id.project_categ_id
            obi_ids = [x.obi_id.id for x in project_line.budget_line]
            return {'domain': {'obi_id': [('id', 'in', obi_ids)]},
                    'value': {'account_id': account.id or False,
                              'project_id': project.id or False,
                              'project_categ_id': categ.id or False,
                              'obi_id': obi_ids and obi_ids[0] or False,
                              }}
        # Case 2: If choose account_id, get first project line, then get info
        if account_id and not project_line_id:
            project_lines = obj.search([('account_id', '=', account_id)])
            if project_lines:
                project_line = project_lines[0]
                project = project_line.project_id
                categ = project_line.project_id.project_categ_id
                obi_ids = [x.obi_id.id for x in project_line.budget_line]
                return {'domain': {'obi_id': [('id', 'in', obi_ids)]},
                        'value': {'project_line_id': project_line.id or False,
                                  'project_id': project.id or False,
                                  'project_categ_id': categ.id or False,
                                  'obi_id': obi_ids and obi_ids[0] or False,
                                  }}
        return {'value': {}}

    @api.multi
    def onchange_obi_id(self, obi_id, description):
        if not obi_id:
            return {'value': {'name': description}}
        obj_obi = self.env['npo.obi']
        obi = obj_obi.browse(obi_id)
        return {'value': {'name': obi.name}}

    @api.multi
    def onchange_qty_price(self, cash_type, quantity, unit_price):
        quantity = quantity or 0.0
        unit_price = unit_price or 0.0
        amount = quantity * unit_price * (cash_type == 'cashin' and 1 or -1)
        return {'value': {'amount': amount}}

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
