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

from openerp import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

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
    description = fields.Char(
        string='Description',
        size=256,
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
