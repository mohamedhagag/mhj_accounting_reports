/** @odoo-module **/

import { registry } from "@web/core/registry";
import { onMounted, useRef } from "@odoo/owl";
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
        if (!data || !data.lines || data.lines.length === 0) return;

        // Calculate totals: Assets vs Liabilities + Equity
        let assets = 0, liabilities = 0, equity = 0;
        
        (data.lines || []).forEach(line => {
            const lineName = (line.name || '').toLowerCase();
            const balance = parseFloat(line.balance || 0);
            
            if (lineName.includes('asset')) {
                assets += balance;
            } else if (lineName.includes('liability') || lineName.includes('liabilities')) {
                liabilities += balance;
            } else if (lineName.includes('equity')) {
                equity += balance;
            }
        });

        const ctx = this.chartRef.el.getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Assets', 'Liabilities', 'Equity'],
                datasets: [{
                    data: [Math.abs(assets), Math.abs(liabilities), Math.abs(equity)],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(255, 206, 86, 0.6)',
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(255, 206, 86, 1)',
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
                        text: 'Balance Sheet Composition'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    async loadReport() {
        await super.loadReport();
        if (this.state.reportData) {
            this.renderChart();
        }
    }
}

registry.category("actions").add("mhj_balance_sheet_interactive", BalanceSheetReport);
