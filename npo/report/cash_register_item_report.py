# -*- coding: utf-8 -*-

from openerp import tools
from openerp import fields, models, api


class CashRegisterItemReport(models.Model):
    _name = "cash.register.item.report"
    _description = "Cash Register Items Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    period_id = fields.Many2one(
        'account.period',
        string='Period',
    )
    date = fields.Date(
        string='Date',
    )
    year = fields.Char(
        string='Year',
        size=4,
        readonly=True,
    )
    day = fields.Char(
        string='Day',
        size=128,
        readonly=True,
    )
    month = fields.Selection(
        [('01', 'January'), ('02', 'February'), ('03', 'March'),
         ('04', 'April'), ('05', 'May'), ('06', 'June'),
         ('07', 'July'), ('08', 'August'), ('09', 'September'),
         ('10', 'October'), ('11', 'November'), ('12', 'December')],
        string='Month',
        readonly=True)
    cash_type = fields.Selection(
        [('cashin', 'In'),
         ('cashout', 'Out')],
        string='In/Out')
    project_line_id = fields.Many2one(
        'npo.project.line',
        string='Line',
    )
    obi_id = fields.Many2one(
        'npo.obi',
        string='Donor',
    )
    name = fields.Char(
        string='OBI',
        help="Originator to Beneficiary Information",
    )
    obi_dest_id = fields.Many2one(
        'npo.obi',
        string='Rpt Donor',
    )
    doc_number = fields.Char(
        string='Ref#',
    )
    project_categ_id = fields.Many2one(
        'npo.project.categ',
        string='Project Categ',
    )
    project_id = fields.Many2one(
        'npo.project',
        string='Project',
    )
    ref = fields.Char(
        string='Reference',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
    )
    description = fields.Char(
        string='Description',
    )
    purpose = fields.Char(
        string='Purpose',
    )
    activity_id = fields.Many2one(
        'npo.activity',
        string='Activity',
    )
    account_id = fields.Many2one(
        'account.account',
        string='Account',
    )
    quantity = fields.Float(
        string='Quantity',
    )
    unit_price = fields.Float(
        string='Unit Price',
    )
    amount = fields.Float(
        string='Amount',
    )

    def init(self, cr):
        # self._table = sale_invoice_payment_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""
        CREATE or REPLACE VIEW cash_register_item_report as (
        select head.period_id, line.id, line.date, line.cash_type,
        line.project_line_id, line.obi_id, line.name, line.obi_dest_id,
        line.doc_number, line.project_categ_id, line.project_id,
        line.ref, line.partner_id, line.description, line.purpose,
        line.activity_id, line.account_id, line.quantity,
        line.unit_price, line.amount,
        to_char(line.date::timestamp with time zone, 'YYYY'::text) AS year,
        to_char(line.date::timestamp with time zone, 'MM'::text) AS month,
        to_char(line.date::timestamp with time zone, 'YYYY-MM-DD'::text) AS day
        from account_bank_statement_line line
        join account_bank_statement head on head.id = line.statement_id
        )""")
