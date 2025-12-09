/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { FinancialReportBase } from "./financial_reports";

/**
 * Trial Balance Report Component
 */
export class TrialBalanceReport extends FinancialReportBase {
    static contentTemplate = "mhj_account_reports.TrialBalanceReportContent";
    static props = {
        ...FinancialReportBase.props,
    };

    setup() {
        super.setup();
        this.reportType = 'trial_balance';
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
        if (!data || !data.totals) return;

        const ctx = this.chartRef.el.getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Initial Balance', 'Period Activity', 'Ending Balance'],
                datasets: [
                    {
                        label: 'Debit',
                        data: [
                            parseFloat(data.totals.initial_debit || 0),
                            parseFloat(data.totals.period_debit || 0),
                            parseFloat(data.totals.ending_debit || 0),
                        ],
                        backgroundColor: 'rgba(75, 192, 192, 0.6)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Credit',
                        data: [
                            parseFloat(data.totals.initial_credit || 0),
                            parseFloat(data.totals.period_credit || 0),
                            parseFloat(data.totals.ending_credit || 0),
                        ],
                        backgroundColor: 'rgba(255, 99, 132, 0.6)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Trial Balance - Debit vs Credit'
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString('en-US', {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                });
                            }
                        }
                    }
                }
            }
        });
    }

    async loadReport() {
        await super.loadReport();
        if (this.chartRef.el && this.state.reportData) {
            this.renderChart();
        }
    }
}

registry.category("actions").add("mhj_trial_balance_interactive", TrialBalanceReport);
