/** @odoo-module **/

import { useState, onMounted, useRef } from "@odoo/owl";
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
        this.chartRef = useRef("chart");

        onMounted(() => {
            if (this.state.reportData) {
                this.renderChart();
            }
        });
    }

    renderChart() {
        if (!this.chartRef.el || !window.Chart) return;

        const data = this.state.reportData;
        if (!data || !data.partners || data.partners.length === 0) return;

        // Get top 10 partners by outstanding balance
        const topPartners = data.partners
            .sort((a, b) => Math.abs(b.total_balance || 0) - Math.abs(a.total_balance || 0))
            .slice(0, 10);

        const ctx = this.chartRef.el.getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: topPartners.map(p => (p.name || '').substring(0, 20)),
                datasets: [{
                    data: topPartners.map(p => Math.abs(parseFloat(p.total_balance || 0))),
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(255, 206, 86, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(153, 102, 255, 0.6)',
                        'rgba(255, 159, 64, 0.6)',
                        'rgba(75, 192, 192, 0.4)',
                        'rgba(255, 99, 132, 0.4)',
                        'rgba(255, 206, 86, 0.4)',
                        'rgba(54, 162, 235, 0.4)',
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(54, 162, 235, 1)',
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Top 10 Partners by Outstanding Balance'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
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
        if (this.state.reportData) {
            this.renderChart();
        }
    }
}

registry.category("actions").add("mhj_partner_ledger_interactive", PartnerLedgerReport);
