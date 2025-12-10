/** @odoo-module **/

/**
 * HTML to Excel Converter for Financial Reports
 * Converts on-screen HTML tables to formatted Excel workbooks
 * 
 * Features:
 * - Preserves HTML table structure exactly as displayed
 * - Maintains cell formatting and styling
 * - Auto-adjusts column widths
 * - Applies borders and colors
 * - Handles merged cells
 * - Supports multi-sheet workbooks
 */
export class HtmlToExcelConverter {
    constructor() {
        // Wait for XLSX to be available, don't fail at import time
        this.XLSX = window.XLSX;
    }

    /**
     * Verify XLSX is loaded before use
     */
    _ensureXLSX() {
        if (!window.XLSX) {
            throw new Error('XLSX library not loaded. Please ensure xlsx library is loaded in assets.');
        }
        this.XLSX = window.XLSX;
        return this.XLSX;
    }

    /**
     * Convert HTML table to Excel workbook
     * @param {string} htmlTableId - ID of HTML table element or class selector
     * @param {string} sheetName - Name for the Excel sheet
     * @param {object} options - Additional options
     * @returns {Workbook} XLSX workbook object
     */
    convertTableToSheet(htmlTableId, sheetName = 'Sheet1', options = {}) {
        const XLSX = this._ensureXLSX();
        const tableElement = document.getElementById(htmlTableId) || document.querySelector(htmlTableId);
        if (!tableElement) {
            throw new Error(`Table element not found: ${htmlTableId}`);
        }

        const rows = [];
        const mergedCells = [];
        let maxCol = 0;

        // Parse table rows
        const tableRows = tableElement.querySelectorAll('tr');
        let rowIndex = 0;

        tableRows.forEach((tr, trIndex) => {
            const rowData = [];
            const cells = tr.querySelectorAll('td, th');
            let colIndex = 0;

            cells.forEach((cell) => {
                const value = this._getCellValue(cell);
                const colspan = parseInt(cell.getAttribute('colspan') || '1');
                const rowspan = parseInt(cell.getAttribute('rowspan') || '1');

                // Add cell value
                rowData[colIndex] = value;

                // Track merged cells
                if (colspan > 1 || rowspan > 1) {
                    mergedCells.push({
                        s: { r: rowIndex, c: colIndex },
                        e: { r: rowIndex + rowspan - 1, c: colIndex + colspan - 1 }
                    });
                }

                colIndex += colspan;
            });

            if (rowData.length > maxCol) {
                maxCol = rowData.length;
            }

            rows.push(rowData);
            rowIndex++;
        });

        // Create worksheet
        const ws = XLSX.utils.aoa_to_sheet(rows);

        // Apply styling
        if (!ws['!cols']) ws['!cols'] = [];
        ws['!cols'] = this._autoAdjustColumns(rows, maxCol);

        // Apply merged cells
        if (mergedCells.length > 0) {
            ws['!merges'] = mergedCells;
        }

        // Apply cell styles
        this._applyCellStyles(ws, tableElement, rows.length);

        return ws;
    }

    /**
     * Convert multiple tables to workbook with multiple sheets
     * @param {Array<{selector: string, sheetName: string}>} tables - Array of table configs
     * @returns {Workbook} XLSX workbook with multiple sheets
     */
    convertMultipleTablesToWorkbook(tables) {
        const XLSX = this._ensureXLSX();
        const workbook = XLSX.utils.book_new();

        tables.forEach(({ selector, sheetName }) => {
            const worksheet = this.convertTableToSheet(selector, sheetName);
            XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
        });

        return workbook;
    }

    /**
     * Convert entire financial report to Excel
     * Captures all visible tables on the page
     * @param {string} reportTitle - Title for the workbook
     * @returns {Workbook} XLSX workbook
     */
    convertEntireReportToWorkbook(reportTitle = 'Financial Report') {
        const XLSX = this._ensureXLSX();
        const workbook = XLSX.utils.book_new();
        
        // Try multiple selectors for compatibility
        let contentArea = document.querySelector('.financial-report-container') ||
                         document.querySelector('.mhj_report_content') ||
                         document.querySelector('.o_content');
        
        if (!contentArea) {
            throw new Error('Report content area not found. Expected element with class "financial-report-container", "mhj_report_content", or "o_content"');
        }

        // Find all tables in the report
        const tables = contentArea.querySelectorAll('table');
        let sheetIndex = 1;

        tables.forEach((table) => {
            try {
                // Get table context (title, section name, etc.)
                const context = this._getTableContext(table);
                const sheetName = context || `Sheet${sheetIndex}`;
                
                // Create sheet from table
                const worksheet = this._tableToWorksheet(table, sheetName);
                XLSX.utils.book_append_sheet(workbook, worksheet, sheetName.substring(0, 31)); // Excel sheet name limit
                
                sheetIndex++;
            } catch (error) {
                console.warn('Failed to convert table to sheet:', error);
            }
        });

        if (sheetIndex === 1) {
            throw new Error('No tables found in report content');
        }

        return workbook;
    }

    /**
     * Download workbook as Excel file
     * @param {Workbook} workbook - XLSX workbook object
     * @param {string} filename - Output filename (without extension)
     */
    downloadWorkbook(workbook, filename = 'report') {
        const timestamp = new Date().toISOString().slice(0, 10);
        const fullFilename = `${filename}_${timestamp}.xlsx`;
        this.XLSX.writeFile(workbook, fullFilename);
    }

    /**
     * Download from on-screen report directly
     * @param {string} filename - Output filename
     */
    downloadReportAsExcel(filename = 'financial_report') {
        try {
            const workbook = this.convertEntireReportToWorkbook();
            this.downloadWorkbook(workbook, filename);
        } catch (error) {
            throw new Error(`Failed to export report: ${error.message}`);
        }
    }

    /**
     * Internal: Convert table element to worksheet
     */
    _tableToWorksheet(tableElement, sheetName) {
        const XLSX = this._ensureXLSX();
        const rows = [];
        const mergedCells = [];

        // Parse table
        const tableRows = tableElement.querySelectorAll('tr');
        let rowIndex = 0;

        tableRows.forEach((tr) => {
            const rowData = [];
            const cells = tr.querySelectorAll('td, th');
            let colIndex = 0;

            cells.forEach((cell) => {
                const value = this._getCellValue(cell);
                const colspan = parseInt(cell.getAttribute('colspan') || '1');
                const rowspan = parseInt(cell.getAttribute('rowspan') || '1');

                rowData[colIndex] = value;

                if (colspan > 1 || rowspan > 1) {
                    mergedCells.push({
                        s: { r: rowIndex, c: colIndex },
                        e: { r: rowIndex + rowspan - 1, c: colIndex + colspan - 1 }
                    });
                }

                colIndex += colspan;
            });

            rows.push(rowData);
            rowIndex++;
        });

        // Create worksheet
        const ws = XLSX.utils.aoa_to_sheet(rows);

        // Set column widths
        const maxCol = Math.max(...rows.map(r => r.length));
        ws['!cols'] = this._autoAdjustColumns(rows, maxCol);

        // Apply merged cells
        if (mergedCells.length > 0) {
            ws['!merges'] = mergedCells;
        }

        // Apply styling
        this._applyCellStyles(ws, tableElement, rows.length);

        return ws;
    }

    /**
     * Internal: Get cell value from HTML element
     */
    _getCellValue(cell) {
        const text = cell.textContent.trim();
        
        // Check if cell contains primarily numeric content (like currency amounts)
        // Only convert to number if the text is mostly numbers with optional formatting
        const numericOnlyMatch = text.match(/^[-+]?[\d,]+\.?\d*$/); // e.g., "1,234.56" or "-100"
        const currencyMatch = text.match(/^[-+]?[\d,]+\.?\d*\s*[%€$£¥₹]?$/i); // e.g., "1,234.56 €"
        
        if (numericOnlyMatch || currencyMatch) {
            // Try to parse as number (remove currency symbols and commas)
            const num = parseFloat(text.replace(/[^\d.-]/g, ''));
            if (!isNaN(num)) {
                return num;
            }
        }
        
        // Return as text if not a pure number
        return text || '';
    }

    /**
     * Internal: Auto-adjust column widths based on content
     */
    _autoAdjustColumns(rows, maxCol) {
        const columns = [];
        
        for (let i = 0; i < maxCol; i++) {
            let maxLength = 0;
            
            rows.forEach(row => {
                const cell = row[i];
                if (cell) {
                    const length = String(cell).length;
                    if (length > maxLength) {
                        maxLength = length;
                    }
                }
            });
            
            // Add some padding and set minimum width
            columns.push({
                wch: Math.max(12, Math.min(maxLength + 2, 50))
            });
        }
        
        return columns;
    }

    /**
     * Internal: Apply cell styling from HTML attributes
     */
    _applyCellStyles(worksheet, tableElement, rowCount) {
        // Use Excel built-in format codes and custom format strings
        const styles = {
            header: {
                font: { bold: true, color: { rgb: 'FFFFFFFF' } },
                fill: { fgColor: { rgb: 'FF366092' } },
                alignment: { horizontal: 'center', vertical: 'center' },
                border: this._getBorder()
            },
            total: {
                font: { bold: true },
                fill: { fgColor: { rgb: 'FFEEEEEE' } },
                alignment: { horizontal: 'right', vertical: 'center' },
                numFmt: '#,##0.00',  // Custom number format with thousands separator
                border: this._getBorder()
            },
            section: {
                font: { bold: true, color: { rgb: 'FFFFFFFF' } },
                fill: { fgColor: { rgb: 'FF4472C4' } },
                alignment: { horizontal: 'center', vertical: 'center' },
                border: this._getBorder()
            },
            number: {
                alignment: { horizontal: 'right', vertical: 'center' },
                numFmt: '#,##0.00',  // Custom number format with thousands separator
                border: this._getBorder()
            },
            currency: {
                alignment: { horizontal: 'right', vertical: 'center' },
                numFmt: '#,##0.00',  // Custom number format with thousands separator
                border: this._getBorder()
            }
        };

        // First pass: detect which columns contain numeric data
        const numericColumns = this._detectNumericColumns(tableElement, rowCount);

        // Second pass: Apply styles cell by cell
        for (let r = 0; r < rowCount; r++) {
            const tr = tableElement.querySelectorAll('tr')[r];
            if (!tr) continue;

            const cells = tr.querySelectorAll('td, th');
            let colIndex = 0;

            cells.forEach((cell) => {
                const cellRef = this.XLSX.utils.encode_cell({ r, c: colIndex });
                const cellValue = worksheet[cellRef];
                
                if (!cellValue) {
                    colIndex += parseInt(cell.getAttribute('colspan') || '1');
                    return;
                }

                // Determine style based on element classes
                let style = {};
                const classes = cell.className;

                if (cell.tagName === 'TH' || classes.includes('table-primary') || classes.includes('table-dark')) {
                    style = styles.header;
                } else if (classes.includes('fw-bold') || classes.includes('table-success') || classes.includes('table-info')) {
                    style = styles.total;
                } else if (classes.includes('table-')) {
                    style = styles.section;
                } else if (classes.includes('text-end') || numericColumns.has(colIndex)) {
                    // Use currency format for right-aligned or numeric columns
                    style = { ...styles.currency };
                    if (typeof cellValue.v === 'number') {
                        // Explicitly mark as number and set format to ensure thousands separator
                        cellValue.t = 'n';
                        cellValue.z = '#,##0.00';
                    }
                } else if (typeof cellValue.v === 'number') {
                    // Apply number format to any numeric cell
                    style = { ...styles.currency };
                    cellValue.t = 'n';
                    cellValue.z = '#,##0.00';
                }

                if (Object.keys(style).length > 0) {
                    cellValue.s = style;
                }

                colIndex += parseInt(cell.getAttribute('colspan') || '1');
            });
        }
    }

    /**
     * Internal: Detect which columns contain numeric data
     */
    _detectNumericColumns(tableElement, rowCount) {
        const numericColumns = new Set();
        const minNumericRows = Math.max(2, Math.floor(rowCount * 0.5)); // At least 50% of rows should be numeric
        const columnStats = {}; // Track numeric count per column

        for (let r = 0; r < rowCount; r++) {
            const tr = tableElement.querySelectorAll('tr')[r];
            if (!tr) continue;

            const cells = tr.querySelectorAll('td, th');
            let colIndex = 0;

            cells.forEach((cell) => {
                // Skip header rows
                if (r === 0 && cell.tagName === 'TH') {
                    return;
                }

                const text = cell.textContent.trim();
                const isNumeric = /^[-+]?[\d,]+\.?\d*$/.test(text); // Pure number
                const isCurrency = /^[-+]?[\d,]+\.?\d*\s*[%€$£¥₹]?$/i.test(text); // Currency
                const isRightAligned = cell.className.includes('text-end') || 
                                      window.getComputedStyle(cell).textAlign === 'right';

                if (isNumeric || isCurrency || isRightAligned) {
                    if (!columnStats[colIndex]) {
                        columnStats[colIndex] = 0;
                    }
                    columnStats[colIndex]++;
                }

                colIndex += parseInt(cell.getAttribute('colspan') || '1');
            });
        }

        // Mark columns as numeric if they have enough numeric data
        for (const [colIndex, count] of Object.entries(columnStats)) {
            if (count >= minNumericRows) {
                numericColumns.add(parseInt(colIndex));
            }
        }

        return numericColumns;
    }

    /**
     * Internal: Get border configuration
     */
    _getBorder() {
        return {
            top: { style: 'thin' },
            bottom: { style: 'thin' },
            left: { style: 'thin' },
            right: { style: 'thin' }
        };
    }

    /**
     * Internal: Extract table context from surrounding elements
     */
    _getTableContext(tableElement) {
        // Look for heading before table
        let prev = tableElement.previousElementSibling;
        while (prev) {
            if (prev.tagName.match(/^H[1-6]$/)) {
                return prev.textContent.trim().substring(0, 31);
            }
            prev = prev.previousElementSibling;
        }

        // Look in parent card header
        const card = tableElement.closest('.card');
        if (card) {
            const header = card.querySelector('.card-header h3');
            if (header) {
                return header.textContent.trim().substring(0, 31);
            }
        }

        return null;
    }

    /**
     * Static helper: Export from HTML string
     */
    static fromHtmlString(htmlString, sheetName = 'Sheet1') {
        const converter = new HtmlToExcelConverter();
        const XLSX = converter._ensureXLSX();
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlString, 'text/html');
        const table = doc.querySelector('table');
        
        if (!table) {
            throw new Error('No table found in HTML string');
        }

        const rows = [];
        table.querySelectorAll('tr').forEach(tr => {
            const rowData = [];
            tr.querySelectorAll('td, th').forEach(cell => {
                rowData.push(converter._getCellValue(cell));
            });
            rows.push(rowData);
        });

        const ws = XLSX.utils.aoa_to_sheet(rows);
        ws['!cols'] = converter._autoAdjustColumns(rows, rows[0].length);

        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, ws, sheetName);

        return workbook;
    }
}

export default HtmlToExcelConverter;
