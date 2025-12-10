/** @odoo-module **/

import { useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { FinancialReportBase } from "./financial_reports";

/**
 * Profit & Loss Report Component
 */
export class ProfitLossReport extends FinancialReportBase {
    static contentTemplate = "mhj_account_reports.ProfitLossReportContent";
    static props = {
        ...FinancialReportBase.props,
    };

    setup() {
        super.setup();
        this.reportType = "profit_loss";
        this.expanded = useState({});

        onMounted(() => {
            // no chart for P&L; rendering is instantaneous
        });
    }

    toggleLine(lineId) {
        this.expanded[lineId] = !this.expanded[lineId];
    }

    isExpanded(lineId) {
        return !!this.expanded[lineId];
    }

    getLineIndent(level) {
        return (level || 0) * 20;
    }

    getLineClass(line) {
        if (!line.type) return '';
        if (line.type === 'report') return 'fw-bold text-primary';
        if (line.type === 'accounts') return 'text-muted small';
        return '';
    }

    async loadReport() {
        await super.loadReport();
        Object.keys(this.expanded).forEach((key) => delete this.expanded[key]);
    }
}

registry.category("actions").add("mhj_profit_loss_interactive", ProfitLossReport);
