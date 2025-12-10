/** @odoo-module **/

import { onMounted, useState, useRef } from "@odoo/owl";
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
        if (!data || !data.accounts || data.accounts.length === 0) return;

        // Get top 10 accounts by absolute balance for chart
        const topAccounts = data.accounts
            .sort((a, b) => Math.abs(b.balance || 0) - Math.abs(a.balance || 0))
            .slice(0, 10);

        const ctx = this.chartRef.el.getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: topAccounts.map(acc => `${acc.code || ''} - ${(acc.name || '').substring(0, 20)}`),
                datasets: [{
                    label: 'Balance',
                    data: topAccounts.map(acc => parseFloat(acc.balance || 0)),
                    backgroundColor: topAccounts.map(acc => {
                        const balance = parseFloat(acc.balance || 0);
                        return balance >= 0 ? 'rgba(75, 192, 192, 0.6)' : 'rgba(255, 99, 132, 0.6)';
                    }),
                    borderColor: topAccounts.map(acc => {
                        const balance = parseFloat(acc.balance || 0);
                        return balance >= 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)';
                    }),
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Top 10 Accounts by Balance'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString('en-US', {
                                    minimumFractionDigits: 0,
                                    maximumFractionDigits: 0
                                });
                            }
                        }
                    }
                }
            }
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
        if (this.state.reportData) {
            this.renderChart();
        }
    }
}

registry.category("actions").add("mhj_general_ledger_interactive", GeneralLedgerReport);
