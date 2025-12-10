/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FinancialReportBase } from "./financial_reports";

/**
 * Cash Flow Report Component
 */
export class CashFlowReport extends FinancialReportBase {
    static contentTemplate = "mhj_account_reports.CashFlowReportContent";
    static props = {
        ...FinancialReportBase.props,
    };

    setup() {
        super.setup();
        this.reportType = "cash_flow";
    }
}

registry.category("actions").add("mhj_cash_flow_interactive", CashFlowReport);
