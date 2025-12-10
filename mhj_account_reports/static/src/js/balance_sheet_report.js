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
                this.categorizeLines();
                this.renderChart();
            }
        });
    }

    categorizeLines() {
        /**
         * Categorize balance sheet lines into assets and liabilities+equity
         * by tracking hierarchy and keywords
         */
        if (!this.state.reportData || !this.state.reportData.lines) return;

        const lines = this.state.reportData.lines || [];
        let assetsSectionFound = false;
        let liabilitiesSectionFound = false;
        let currentSection = null;

        // Pass 1: Find section headers and mark sections
        lines.forEach((line, index) => {
            const lineName = (line.name || '').toLowerCase().trim();
            
            // Detect main section headers (level 0 or 1, no parent)
            if ((line.level === 0 || line.level === 1) && (!line.parent_id || line.parent_id === null || line.parent_id === false)) {
                if (lineName.includes('asset')) {
                    currentSection = 'assets';
                    assetsSectionFound = true;
                    line._section = 'assets';
                    line._isHeader = true;
                } else if (lineName.includes('liability') || lineName.includes('equity') || lineName.includes('shareholders') || lineName.includes('capital')) {
                    currentSection = 'liabilities';
                    liabilitiesSectionFound = true;
                    line._section = 'liabilities';
                    line._isHeader = true;
                }
            } else {
                // Assign to current section based on hierarchy
                line._section = currentSection || 'unknown';
            }
        });

        // Pass 2: Use section tracking to properly categorize
        let inAssets = false;
        let inLiabilities = false;
        
        lines.forEach(line => {
            const lineName = (line.name || '').toLowerCase().trim();
            
            // Re-detect sections more robustly
            if (line._isHeader && lineName.includes('asset')) {
                inAssets = true;
                inLiabilities = false;
                line._section = 'assets';
            } else if (line._isHeader && (lineName.includes('liability') || lineName.includes('equity'))) {
                inAssets = false;
                inLiabilities = true;
                line._section = 'liabilities';
            } else if (inAssets) {
                line._section = 'assets';
            } else if (inLiabilities) {
                line._section = 'liabilities';
            }
        });
    }

    getAssetLines() {
        return (this.state.reportData?.lines || []).filter(line => line._section === 'assets');
    }

    getLiabilityLines() {
        return (this.state.reportData?.lines || []).filter(line => line._section === 'liabilities');
    }

    renderChart() {
        if (!this.chartRef.el || !window.Chart) return;

        const data = this.state.reportData;
        if (!data || !data.lines || data.lines.length === 0) return;

        // Calculate totals using categorized lines
        let assets = 0, liabilities = 0, equity = 0;
        
        (data.lines || []).forEach(line => {
            const lineName = (line.name || '').toLowerCase();
            const balance = parseFloat(line.balance || 0);
            const section = line._section || '';
            
            if (section === 'assets') {
                assets += balance;
            } else if (section === 'liabilities') {
                if (lineName.includes('equity')) {
                    equity += balance;
                } else {
                    liabilities += balance;
                }
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
            this.categorizeLines();
            this.renderChart();
        }
    }
}

registry.category("actions").add("mhj_balance_sheet_interactive", BalanceSheetReport);
