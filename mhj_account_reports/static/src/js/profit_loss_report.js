/** @odoo-module **/

import { useState, onMounted, useRef } from "@odoo/owl";
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

        // Categorize lines by type
        let revenue = 0, cogs = 0, expenses = 0, other_income = 0;
        
        (data.lines || []).forEach(line => {
            if (!line.name) return;
            const lineName = line.name.toLowerCase();
            const balance = parseFloat(line.balance || 0);
            
            if (lineName.includes('revenue') || lineName.includes('sales') || lineName.includes('income')) {
                revenue += balance;
            } else if (lineName.includes('cost') || lineName.includes('cogs')) {
                cogs += balance;
            } else if (lineName.includes('expense')) {
                expenses += balance;
            } else if (lineName.includes('other')) {
                other_income += balance;
            }
        });

        const grossProfit = revenue - cogs;
        const operatingProfit = grossProfit - expenses;
        const netProfit = operatingProfit + other_income;

        const ctx = this.chartRef.el.getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Revenue', 'COGS', 'Gross Profit', 'Expenses', 'Operating Profit', 'Other Income', 'Net Profit'],
                datasets: [{
                    label: 'P&L Components',
                    data: [revenue, -cogs, grossProfit, -expenses, operatingProfit, other_income, netProfit],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(75, 192, 192, 0.6)',
                        netProfit >= 0 ? 'rgba(75, 192, 192, 0.8)' : 'rgba(255, 99, 132, 0.8)',
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(75, 192, 192, 1)',
                        netProfit >= 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)',
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
                        text: 'Profit & Loss Waterfall'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
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
        if (this.state.reportData) {
            this.renderChart();
        }
    }
}

registry.category("actions").add("mhj_profit_loss_interactive", ProfitLossReport);
