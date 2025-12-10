/** @odoo-module **/

import { useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { FinancialReportBase } from "./financial_reports";

/**
 * Partner Ledger Report Component
 */
export class PartnerLedgerReport extends FinancialReportBase {
    static contentTemplate = "mhj_account_reports.PartnerLedgerReportContent";
    static props = {
        ...FinancialReportBase.props,
    };

    setup() {
        super.setup();
        this.reportType = "partner_ledger";
        this.expanded = useState({});
    }

    togglePartner(partnerId) {
        this.expanded[partnerId] = !this.expanded[partnerId];
    }

    isExpanded(partnerId) {
        return !!this.expanded[partnerId];
    }

    async loadReport() {
        await super.loadReport();
        Object.keys(this.expanded).forEach((key) => delete this.expanded[key]);
    }
}

registry.category("actions").add("mhj_partner_ledger_interactive", PartnerLedgerReport);
