/**
 * Terminal Component
 * Displays engine output, logs, and benchmark results
 */

import { EngineConfig } from '../config.js';

export class Terminal {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Terminal: Container '${containerId}' not found`);
            return;
        }

        this.lines = [];
        this.maxLines = EngineConfig.ui.terminalMaxLines;
        this.autoScroll = EngineConfig.ui.autoScrollTerminal;
        this.showTimestamps = false;

        this.init();
    }

    /**
     * Initialize terminal UI
     */
    init() {
        // Clear existing content
        this.container.innerHTML = '';

        // Create terminal structure
        this.container.className = 'terminal-output';

        // Add initial message
        this.writeLine('DASE Engine Terminal Ready', 'success');
        this.writeLine('Connecting to engine server...', 'info');
    }

    /**
     * Write a line to the terminal
     * @param {string} text - Text to write
     * @param {string} type - Line type (info, success, warning, error, accent, dim)
     */
    writeLine(text, type = 'info') {
        const line = document.createElement('div');
        line.className = `terminal-line terminal-line-${type}`;

        // Add timestamp if enabled
        if (this.showTimestamps) {
            const timestamp = this._getTimestamp();
            const timestampSpan = document.createElement('span');
            timestampSpan.className = 'terminal-timestamp';
            timestampSpan.textContent = timestamp;
            line.appendChild(timestampSpan);
        }

        // Add text content
        const textNode = document.createTextNode(text);
        line.appendChild(textNode);

        // Add to container
        this.container.appendChild(line);
        this.lines.push(line);

        // Limit number of lines
        while (this.lines.length > this.maxLines) {
            const oldLine = this.lines.shift();
            if (oldLine && oldLine.parentNode) {
                oldLine.parentNode.removeChild(oldLine);
            }
        }

        // Auto-scroll if enabled
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }

    /**
     * Write multiple lines at once
     * @param {string[]} lines - Array of lines to write
     * @param {string} type - Line type
     */
    writeLines(lines, type = 'info') {
        lines.forEach(line => this.writeLine(line, type));
    }

    /**
     * Write info message
     * @param {string} text - Text to write
     */
    info(text) {
        this.writeLine(text, 'info');
    }

    /**
     * Write success message
     * @param {string} text - Text to write
     */
    success(text) {
        this.writeLine(text, 'success');
    }

    /**
     * Write warning message
     * @param {string} text - Text to write
     */
    warning(text) {
        this.writeLine(text, 'warning');
    }

    /**
     * Write error message
     * @param {string} text - Text to write
     */
    error(text) {
        this.writeLine(text, 'error');
    }

    /**
     * Write accent message (highlighted)
     * @param {string} text - Text to write
     */
    accent(text) {
        this.writeLine(text, 'accent');
    }

    /**
     * Write dim message (less prominent)
     * @param {string} text - Text to write
     */
    dim(text) {
        this.writeLine(text, 'dim');
    }

    /**
     * Write a separator line
     */
    separator() {
        this.writeLine('─'.repeat(80), 'dim');
    }

    /**
     * Clear the terminal
     */
    clear() {
        this.container.innerHTML = '';
        this.lines = [];
    }

    /**
     * Scroll to bottom of terminal
     */
    scrollToBottom() {
        this.container.scrollTop = this.container.scrollHeight;
    }

    /**
     * Toggle auto-scroll
     * @param {boolean} enabled - Enable auto-scroll
     */
    setAutoScroll(enabled) {
        this.autoScroll = enabled;
    }

    /**
     * Toggle timestamps
     * @param {boolean} enabled - Show timestamps
     */
    setShowTimestamps(enabled) {
        this.showTimestamps = enabled;
    }

    /**
     * Set max lines
     * @param {number} maxLines - Maximum number of lines to keep
     */
    setMaxLines(maxLines) {
        this.maxLines = maxLines;

        // Trim excess lines if needed
        while (this.lines.length > this.maxLines) {
            const oldLine = this.lines.shift();
            if (oldLine && oldLine.parentNode) {
                oldLine.parentNode.removeChild(oldLine);
            }
        }
    }

    /**
     * Display formatted metrics
     * @param {object} metrics - Metrics object
     */
    displayMetrics(metrics) {
        this.separator();
        this.accent('Performance Metrics:');

        if (metrics.ns_per_op !== undefined) {
            this.info(`  Time/Op: ${metrics.ns_per_op.toFixed(2)} ns`);
        }

        if (metrics.ops_per_sec !== undefined) {
            const mOpsPerSec = (metrics.ops_per_sec / 1e6).toFixed(2);
            this.info(`  Throughput: ${mOpsPerSec} M ops/sec`);
        }

        if (metrics.speedup_factor !== undefined) {
            this.info(`  Speedup: ${metrics.speedup_factor.toFixed(2)}x`);
        }

        if (metrics.total_operations !== undefined) {
            const totalOps = metrics.total_operations.toLocaleString();
            this.info(`  Total Ops: ${totalOps}`);
        }

        this.separator();
    }

    /**
     * Display benchmark results
     * @param {object} data - Benchmark data
     */
    displayBenchmarkResults(data) {
        this.separator();
        this.success('Benchmark Complete!');

        if (data.duration !== undefined) {
            this.info(`  Duration: ${data.duration.toFixed(2)} seconds`);
        }

        if (data.throughput !== undefined) {
            const throughputM = (data.throughput / 1e6).toFixed(2);
            this.info(`  Throughput: ${throughputM} M ops/sec`);
        }

        if (data.ns_per_op !== undefined) {
            this.info(`  Time/Op: ${data.ns_per_op.toFixed(2)} ns`);

            // Performance assessment
            const threshold = EngineConfig.performance;
            if (data.ns_per_op < threshold.excellentThreshold) {
                this.success(`  Performance: EXCELLENT ⚡`);
            } else if (data.ns_per_op < threshold.targetNsPerOp) {
                this.success(`  Performance: GOOD ✓`);
            } else if (data.ns_per_op < threshold.warningThreshold) {
                this.warning(`  Performance: ACCEPTABLE`);
            } else {
                this.error(`  Performance: NEEDS IMPROVEMENT`);
            }
        }

        this.separator();
    }

    /**
     * Get current timestamp
     * @returns {string} Formatted timestamp
     * @private
     */
    _getTimestamp() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        return `[${hours}:${minutes}:${seconds}]`;
    }

    /**
     * Export terminal content as text
     * @returns {string} Terminal content
     */
    exportAsText() {
        return this.lines.map(line => line.textContent).join('\n');
    }

    /**
     * Save terminal content to file
     * @param {string} filename - Filename to save as
     */
    saveToFile(filename = 'terminal_output.txt') {
        const content = this.exportAsText();
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();

        URL.revokeObjectURL(url);
    }
}

export default Terminal;
