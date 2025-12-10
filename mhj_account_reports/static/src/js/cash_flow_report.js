/** @odoo-module **/

import { registry } from "@web/core/registry";
import { onMounted, useRef } from "@odoo/owl";
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
        if (!data) return;

        // Build sections from aggregated totals (more reliable than line-level data)
        const sections = {};
        const addSection = (label, value) => {
            const numeric = parseFloat(value || 0);
            if (!isNaN(numeric)) {
                sections[label] = numeric;
            }
        };

        addSection('Operating', data.net_operating ?? this._sumObjectValues(data.operating));
        addSection('Investing', data.net_investing ?? this._sumObjectValues(data.investing));
        addSection('Financing', data.net_financing ?? this._sumObjectValues(data.financing));
        addSection('Unclassified', data.unclassified);

        const ctx = this.chartRef.el.getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(sections),
                datasets: [{
                    label: 'Cash Flow',
                    data: Object.values(sections),
                    backgroundColor: Object.values(sections).map(v => 
                        v >= 0 ? 'rgba(75, 192, 192, 0.6)' : 'rgba(255, 99, 132, 0.6)'
                    ),
                    borderColor: Object.values(sections).map(v => 
                        v >= 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)'
                    ),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    title: {
                        display: true,
                        text: 'Cash Flow by Activity Type'
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

    _sumObjectValues(obj = {}) {
        return Object.values(obj || {}).reduce((acc, val) => acc + (parseFloat(val) || 0), 0);
    }

    async loadReport() {
        await super.loadReport();
        if (this.state.reportData) {
            this.renderChart();
        }
    }
}

registry.category("actions").add("mhj_cash_flow_interactive", CashFlowReport);
