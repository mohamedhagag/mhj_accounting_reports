/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

/**
 * Base Financial Report Component
 * Provides common functionality for all financial reports
 */
export class FinancialReportBase extends Component {
    static template = "mhj_account_reports.FinancialReportBase";
    static components = {};
    
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: Number, optional: true },
        updateActionState: { type: Function, optional: true },
        className: { type: String, optional: true },
        "*": true,
    };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            reportData: null,
            loading: true,
            showDebug: false,
            filters: this.getDefaultFilters(),
            filterData: {},
            showFilters: false,
            filterText: {
                journals: '',
                accounts: '',
                partners: '',
                analytics: '',
            },
            filteredJournals: [],
            filteredAccounts: [],
            filteredPartners: [],
            filteredAnalytics: [],
        });

        onWillStart(async () => {
            await this.loadFilterData();
            this.initializeFilteredData();
            await this.loadReport();
        });
    }

    getDefaultFilters() {
        const today = new Date();
        const firstDayOfYear = new Date(today.getFullYear(), 0, 1);
        
        return {
            date_from: this.formatDate(firstDayOfYear),
            date_to: this.formatDate(today),
            state: 'posted',
            display_account: 'all',
            journal_ids: [],
            account_ids: [],
            partner_ids: [],
            analytic_account_ids: [],
        };
    }

    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    async loadFilterData() {
        try {
            console.log('Loading filter data...');
            const result = await rpc('/mhj/accounting_reports/get_filter_data');
            console.log('Filter data received:', result);
            this.state.filterData = result || {};
        } catch (error) {
            this.notification.add("Failed to load filter data: " + (error.message || error), { type: "danger" });
            console.error("Filter data error:", error);
            this.state.filterData = {};
        }
    }

    async loadReport() {
        this.state.loading = true;
        try {
            console.log('Loading report:', this.reportType, 'with filters:', this.state.filters);
            const result = await rpc('/mhj/accounting_reports/get_data', {
                report_type: this.reportType,
                filters: this.state.filters,
            });
            
            console.log('=== RPC Response ===');
            console.log('Response received:', result);
            console.log('Response type:', typeof result);
            console.log('Is null?', result === null);
            console.log('Is undefined?', result === undefined);
            
            if (result) {
                console.log('Response keys:', Object.keys(result));
                console.log('Has accounts:', !!result.accounts);
                console.log('Accounts count:', result?.accounts?.length || 0);
                if (result?.accounts?.length > 0) {
                    console.log('First account:', result.accounts[0]);
                }
            }
            
            if (result && result.error) {
                console.error('Error returned:', result.error);
                this.notification.add("Error: " + result.error, { type: "danger" });
                this.state.reportData = null;
            } else if (result) {
                this.state.reportData = result;
                console.log('✓ Report data set successfully');
            } else {
                console.error('RPC returned null/undefined!');
                this.state.reportData = null;
            }
        } catch (error) {
            this.notification.add("Failed to load report data: " + (error.message || error), { type: "danger" });
            console.error("Report data error:", error);
            this.state.reportData = null;
        } finally {
            this.state.loading = false;
        }
    }

    async applyFilters() {
        await this.loadReport();
        this.state.showFilters = false;
    }

    async resetFilters() {
        this.state.filters = this.getDefaultFilters();
        await this.loadReport();
    }

    toggleFilters() {
        this.state.showFilters = !this.state.showFilters;
    }

    initializeFilteredData() {
        this.state.filteredJournals = this.state.filterData?.journals || [];
        this.state.filteredAccounts = this.state.filterData?.accounts || [];
        this.state.filteredPartners = this.state.filterData?.partners || [];
        this.state.filteredAnalytics = this.state.filterData?.analytic_accounts || [];
    }

    filterItems(type) {
        const searchText = this.state.filterText[type].toLowerCase();
        let sourceData = [];
        let targetKey = '';

        if (type === 'journals') {
            sourceData = this.state.filterData?.journals || [];
            targetKey = 'filteredJournals';
        } else if (type === 'accounts') {
            sourceData = this.state.filterData?.accounts || [];
            targetKey = 'filteredAccounts';
        } else if (type === 'partners') {
            sourceData = this.state.filterData?.partners || [];
            targetKey = 'filteredPartners';
        } else if (type === 'analytics') {
            sourceData = this.state.filterData?.analytic_accounts || [];
            targetKey = 'filteredAnalytics';
        }

        if (searchText) {
            this.state[targetKey] = sourceData.filter(item => {
                const nameMatch = item.name?.toLowerCase().includes(searchText);
                const codeMatch = item.code?.toLowerCase().includes(searchText);
                return nameMatch || codeMatch;
            });
        } else {
            this.state[targetKey] = sourceData;
        }
    }

    toggleItem(filterKey, itemId, itemName) {
        if (!this.state.filters[filterKey]) {
            this.state.filters[filterKey] = [];
        }
        
        const index = this.state.filters[filterKey].indexOf(itemId);
        if (index > -1) {
            this.state.filters[filterKey].splice(index, 1);
        } else {
            this.state.filters[filterKey].push(itemId);
        }
    }

    clearFilter(filterKey) {
        this.state.filters[filterKey] = [];
    }

    formatNumber(value) {
        if (value === null || value === undefined) return '0.00';
        return parseFloat(value).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    async exportExcel() {
        this.notification.add("Excel export functionality coming soon", { type: "info" });
    }

    async printReport() {
        this.notification.add("Print functionality coming soon", { type: "info" });
    }
}
