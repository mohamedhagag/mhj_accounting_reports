/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FinancialReportBase } from "./financial_reports";

/**
 * Balance Sheet Report Component
 */
export class BalanceSheetReport extends FinancialReportBase {
    static contentTemplate = "mhj_account_reports.BalanceSheetReportContent";
    static props = {
        ...FinancialReportBase.props,
    };

    setup() {
        super.setup();
        this.reportType = "balance_sheet";
    }
}

registry.category("actions").add("mhj_balance_sheet_interactive", BalanceSheetReport);
