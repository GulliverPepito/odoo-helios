# -*- coding: utf-8 -*-
###################################################################################
#
#    Intellego-BI.com
#    Copyright (C) 2017-TODAY Intellego Business Intelligence S.A.(<http://www.intellego-bi.com>).
#    Author: Rodolfo Bermúdez Neubauer(<https://www.intellego-bi.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
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
###################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo.tools.translate import _




class HrPayslipAnalytic(models.Model):
    _inherit = 'hr.payslip'

    date = fields.Date('Date Account', states={'draft': [('readonly', False)]}, readonly=True,
        help="Keep empty to use the period of the validation(Payslip) date.")
    journal_id = fields.Many2one('account.journal', 'Salary Journal', readonly=True, required=True,
        states={'draft': [('readonly', False)]}, default=lambda self: self.env['account.journal'].search([('type', '=', 'general')], limit=1))
    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)

    @api.model
    def create(self, vals):
        if 'journal_id' in self.env.context:
            vals['journal_id'] = self.env.context.get('journal_id')
        return super(HrPayslipAnalytic, self).create(vals)

    @api.onchange('contract_id')
    def onchange_contract(self):
        super(HrPayslipAnalytic, self).onchange_contract()
        self.journal_id = self.contract_id.journal_id.id or (not self.contract_id and self.default_get(['journal_id'])['journal_id'])

    @api.multi
    def action_payslip_cancel(self):
        moves = self.mapped('move_id')
        moves.filtered(lambda x: x.state == 'posted').button_cancel()
        moves.unlink()
        return super(HrPayslipAnalytic, self).action_payslip_cancel()

    @api.multi
    def compute_sheet(self):
        for payslip in self:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines, 'number': number})
        return True

    @api.multi
    def action_payslip_done(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')
        self.compute_sheet()

        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
            }
            for line in slip.details_by_salary_rule_category:
                cost_center = False 
                no_cost_center = False # Insert Rodolfo Bermudez
                amount = slip.credit_note and -line.total or line.total
                if float_is_zero(amount, precision_digits=precision):
                    continue
                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id
                cost_center = line.salary_rule_id.analytic_account_id.id

                if line.salary_rule_id.account_analytic_true:
                    cost_center = slip.contract_id.analytic_account_id.id
                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_account_id': cost_center,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_account_id': no_cost_center, # Insert Rodolfo Bermúdez 
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line) # Insert Rodolfo Bermudez
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': date})
            move.post()
            # We set the state to done and dont call the Super Class to avoid double posting
            return self.write({'state': 'done'})
    

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    account_analytic_true = fields.Boolean('Analytic Account in Contract')


