/** @odoo-module **/

import { onMounted, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { FinancialReportBase } from "./financial_reports";

/**
 * General Ledger Report Component
 */
export class GeneralLedgerReport extends FinancialReportBase {
    static contentTemplate = "mhj_account_reports.GeneralLedgerReportContent";
    static props = {
        ...FinancialReportBase.props,
    };

    setup() {
        super.setup();
        this.reportType = "general_ledger";
        this.expanded = useState({});

        onMounted(() => {
            // no chart for GL; toggle rendering is instantaneous
        });
    }

    toggleAccount(accountId) {
        this.expanded[accountId] = !this.expanded[accountId];
    }

    isExpanded(accountId) {
        return !!this.expanded[accountId];
    }

    async loadReport() {
        await super.loadReport();
        // Reset expansions after refresh
        Object.keys(this.expanded).forEach((key) => delete this.expanded[key]);
    }
}

registry.category("actions").add("mhj_general_ledger_interactive", GeneralLedgerReport);
