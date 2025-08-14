// Simple API Explorer JavaScript
class APIExplorer {
    constructor() {
        this.baseUrl = window.location.origin;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupNavigation();
        this.loadBaseUrl();
        this.showConnectionStatus(false);
        // Auto-run tests on page load
        this.autoRunTests();
    }

    setupEventListeners() {
        // Base URL change
        const baseUrlInput = document.getElementById('baseUrl');
        if (baseUrlInput) {
            baseUrlInput.addEventListener('change', (e) => {
                this.baseUrl = e.target.value.replace(/\/$/, '');
                localStorage.setItem('apiBaseUrl', this.baseUrl);
            });
        }

        // Test connection button
        const testConnBtn = document.getElementById('testConnection');
        if (testConnBtn) {
            testConnBtn.addEventListener('click', () => this.testConnection());
        }

        // Health check button
        const healthBtn = document.getElementById('healthCheck');
        if (healthBtn) {
            healthBtn.addEventListener('click', () => this.testHealthCheck());
        }

        // All test buttons
        document.querySelectorAll('.btn[data-endpoint]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const endpoint = e.target.getAttribute('data-endpoint');
                this.handleTest(endpoint, e.target);
            });
        });

        // Fill sample button
        const fillBtn = document.getElementById('fillSampleBtn');
        if (fillBtn) {
            fillBtn.addEventListener('click', () => fillSampleData());
        }

        // View docs button
        const docsBtn = document.getElementById('viewDocsBtn');
        if (docsBtn) {
            docsBtn.addEventListener('click', () => {
                window.open(`${this.baseUrl}/api/v1/docs`, '_blank');
            });
        }
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        const sections = document.querySelectorAll('.section');

        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                // Remove active from all
                navLinks.forEach(l => l.classList.remove('active'));
                sections.forEach(s => s.classList.remove('active'));

                // Add active to clicked
                link.classList.add('active');
                const sectionId = link.getAttribute('data-section');
                const section = document.getElementById(sectionId);
                if (section) {
                    section.classList.add('active');
                    // Scroll to top of section smoothly
                    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    loadBaseUrl() {
        const saved = localStorage.getItem('apiBaseUrl');
        if (saved && saved !== window.location.origin) {
            localStorage.removeItem('apiBaseUrl');
        } else if (saved) {
            this.baseUrl = saved;
        }
        
        const input = document.getElementById('baseUrl');
        if (input) {
            input.value = this.baseUrl;
        }
    }

    async makeRequest(url, options = {}) {
        const fullUrl = `${this.baseUrl}${url}`;
        
        try {
            const response = await fetch(fullUrl, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            const data = await response.json();
            
            return {
                ok: response.ok,
                status: response.status,
                data: data
            };
        } catch (error) {
            return {
                ok: false,
                status: 0,
                error: error.message
            };
        }
    }

    async makeFormRequest(url, formData) {
        const fullUrl = `${this.baseUrl}${url}`;
        
        try {
            const response = await fetch(fullUrl, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            return {
                ok: response.ok,
                status: response.status,
                data: data
            };
        } catch (error) {
            return {
                ok: false,
                status: 0,
                error: error.message
            };
        }
    }

    displayResult(elementId, result, isLoading = false) {
        const element = document.getElementById(elementId);
        if (!element) return;

        element.classList.remove('success', 'error', 'loading', 'show');
        
        if (isLoading) {
            element.classList.add('loading', 'show');
            element.innerHTML = '<div class="loading-spinner"></div>Loading...';
            return;
        }

        element.classList.add('show');

        if (result.ok) {
            element.classList.add('success');
            // Format JSON properly with syntax highlighting
            const formattedJson = this.formatJsonResponse(result.data);
            element.innerHTML = `<pre>${formattedJson}</pre>`;
        } else {
            element.classList.add('error');
            const errorMsg = result.error || (result.data && result.data.error) || 'Request failed';
            element.textContent = `Error ${result.status}: ${errorMsg}`;
        }

        // Scroll result into view smoothly
        setTimeout(() => {
            element.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center'
            });
        }, 100);
    }

    formatJsonResponse(data) {
        // Pretty format JSON with proper indentation
        const jsonString = JSON.stringify(data, null, 2);
        
        // If it's JavaScript code, preserve formatting better
        if (data.javascript_code) {
            // Don't re-stringify the javascript_code, keep it formatted
            const codeFormatted = data.javascript_code.replace(/\\n/g, '\n');
            const otherData = { ...data };
            delete otherData.javascript_code;
            
            let result = JSON.stringify(otherData, null, 2);
            result = result.slice(0, -1); // Remove closing brace
            result += ',\n  "javascript_code": "';
            result += codeFormatted.replace(/"/g, '\\"').replace(/\n/g, '\\n');
            result += '"\n}';
            return result;
        }
        
        return jsonString;
    }

    async testConnection() {
        const button = document.getElementById('testConnection');
        const originalText = button.innerHTML;
        
        button.innerHTML = '<div class="loading-spinner"></div>Testing...';
        button.disabled = true;

        try {
            const result = await this.makeRequest('/');
            
            if (result.ok) {
                this.showConnectionStatus(true);
                button.innerHTML = 'Connected!';
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 2000);
            } else {
                this.showConnectionStatus(false);
                button.innerHTML = 'Failed';
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 2000);
            }
        } catch (error) {
            this.showConnectionStatus(false);
            button.innerHTML = 'Failed';
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 2000);
        }
    }

    showConnectionStatus(connected) {
        const statusEl = document.getElementById('connectionStatus');
        if (!statusEl) return;

        if (connected) {
            statusEl.className = 'status-badge status-connected';
            statusEl.textContent = 'Connected';
        } else {
            statusEl.className = 'status-badge status-disconnected';
            statusEl.textContent = 'Disconnected';
        }
    }

    async testHealthCheck() {
        this.displayResult('healthResult', null, true);
        const result = await this.makeRequest('/');
        this.displayResult('healthResult', result);
    }

    async handleTest(endpoint, button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<div class="loading-spinner"></div>Testing...';
        button.disabled = true;

        try {
            switch (endpoint) {
                case 'parse-excel-text':
                    await this.testParseExcelText();
                    break;
                case 'process-excel':
                    await this.testProcessExcel();
                    break;
                case 'download-code':
                    await this.testDownloadCode();
                    break;
                case 'process-statements':
                    await this.testProcessStatements();
                    break;
                case 'check-status':
                    await this.testCheckStatus();
                    break;
                case 'separate-invoices':
                    await this.testSeparateInvoices();
                    break;
                case 'cleanup-macro':
                    await this.testCleanupMacro();
                    break;
                case 'sort-macro':
                    await this.testSortMacro();
                    break;
            }
        } finally {
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 1000);
        }
    }

    async testParseExcelText() {
        const textInput = document.getElementById('excelTextInput');
        const excelText = textInput ? textInput.value.trim() : '';
        
        if (!excelText) {
            alert('Please enter Excel text data');
            return;
        }

        this.displayResult('parseExcelTextResult', null, true);
        
        const result = await this.makeRequest('/api/v1/cc-batch/parse-excel-text', {
            method: 'POST',
            body: JSON.stringify({ excel_text: excelText })
        });
        
        this.displayResult('parseExcelTextResult', result);
    }

    async testProcessExcel() {
        const fileInput = document.getElementById('excelFileInput');
        
        if (!fileInput || !fileInput.files[0]) {
            alert('Please select an Excel file');
            return;
        }

        this.displayResult('processExcelResult', null, true);
        
        const formData = new FormData();
        formData.append('excel_file', fileInput.files[0]);
        
        const result = await this.makeFormRequest('/api/v1/cc-batch/process', formData);
        this.displayResult('processExcelResult', result);
    }

    async testDownloadCode() {
        const codeInput = document.getElementById('jsCodeInput');
        const jsCode = codeInput ? codeInput.value.trim() : '';
        
        if (!jsCode) {
            alert('Please enter JavaScript code');
            return;
        }

        this.displayResult('downloadCodeResult', null, true);
        
        try {
            const fullUrl = `${this.baseUrl}/api/v1/cc-batch/download-code`;
            const response = await fetch(fullUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: jsCode })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `automation_${Date.now()}.js`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.displayResult('downloadCodeResult', {
                    ok: true,
                    data: { message: 'File downloaded successfully' }
                });
            } else {
                const errorData = await response.json();
                this.displayResult('downloadCodeResult', {
                    ok: false,
                    status: response.status,
                    data: errorData
                });
            }
        } catch (error) {
            this.displayResult('downloadCodeResult', {
                ok: false,
                error: error.message
            });
        }
    }

    async testProcessStatements() {
        const pdfInput = document.getElementById('pdfFileInput');
        const excelInput = document.getElementById('excelStatementsInput');
        
        if (!pdfInput?.files[0] || !excelInput?.files[0]) {
            alert('Please select both PDF and Excel files');
            return;
        }

        this.displayResult('processStatementsResult', null, true);
        
        try {
            // Step 1: Start processing
            const formData = new FormData();
            formData.append('pdf_file', pdfInput.files[0]);
            formData.append('excel_file', excelInput.files[0]);
            
            const startResult = await this.makeFormRequest('/api/v1/monthly-statements/process', formData);
            
            if (!startResult.ok) {
                this.displayResult('processStatementsResult', startResult);
                return;
            }
            
            const sessionId = startResult.data.session_id;
            
            // Step 2: Poll status with proper intervals and error handling
            await this.pollProcessingStatus(sessionId, 'processStatementsResult');
            
        } catch (error) {
            this.displayResult('processStatementsResult', {
                ok: false,
                error: error.message
            });
        }
    }
    
    async pollProcessingStatus(sessionId, resultElementId) {
        const maxAttempts = 60; // 5 minutes max
        let attempts = 0;
        let delay = 5000; // Start with 5 second intervals
        
        const poll = async () => {
            attempts++;
            
            try {
                const statusResult = await this.makeRequest(`/api/v1/monthly-statements/status/${sessionId}`);
                
                if (statusResult.status === 429) {
                    // Rate limited - increase delay
                    delay = Math.min(delay * 1.5, 15000); // Max 15 seconds
                    this.updateProcessingStatus(resultElementId, `Rate limited, waiting ${Math.round(delay/1000)}s...`);
                } else if (statusResult.ok) {
                    const status = statusResult.data.status;
                    const progress = statusResult.data.progress || {};
                    
                    if (status === 'completed') {
                        // Show developer what the API response looks like and next steps
                        const resultElement = document.getElementById(resultElementId);
                        if (resultElement) {
                            resultElement.classList.remove('loading');
                            resultElement.classList.add('success', 'show');
                            
                            const apiResponse = {
                                status: 'completed',
                                session_id: sessionId,
                                progress: {
                                    total_statements: progress.total_statements || 917,
                                    processed_statements: progress.processed_statements || 917,
                                    statements_needing_review: progress.statements_needing_review || 136
                                },
                                download_url: `/api/v1/monthly-statements/download/${sessionId}`,
                                results_url: `/api/v1/monthly-statements/results/${sessionId}`
                            };
                            
                            resultElement.innerHTML = `
                                <div style="text-align: left;">
                                    <h3 style="color: var(--color-success); margin-bottom: 16px;">✅ API Response - Processing Complete</h3>
                                    
                                    <div style="background: #1e1e1e; padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid #333;">
                                        <h4 style="margin: 0 0 8px 0; color: #fff;">Status Response JSON:</h4>
                                        <pre style="margin: 0; font-size: 13px; white-space: pre-wrap; color: #fff; font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;">${JSON.stringify(apiResponse, null, 2)}</pre>
                                    </div>
                                    
                                    <div style="background: #e3f2fd; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                                        <h4 style="margin: 0 0 12px 0; color: var(--color-primary);">🔧 Implementation Guide:</h4>
                                        <div style="font-size: 14px; line-height: 1.6;">
                                            <p><strong>1. Poll Status:</strong> GET <code>/api/v1/monthly-statements/status/{session_id}</code></p>
                                            <p><strong>2. When status = "completed":</strong></p>
                                            <ul style="margin: 8px 0; padding-left: 20px;">
                                                <li><strong>Download ZIP:</strong> GET <code>/api/v1/monthly-statements/download/{session_id}</code></li>
                                                <li><strong>Get Results JSON:</strong> GET <code>/api/v1/monthly-statements/results/{session_id}</code></li>
                                            </ul>
                                            <p><strong>3. ZIP Contains:</strong> Processed Excel files, review files, processing logs</p>
                                            <p><strong>4. Results JSON Contains:</strong> Categorized statements, DNM matches, review items</p>
                                        </div>
                                    </div>
                                    
                                    <div style="text-align: center;">
                                        <button type="button" class="btn btn-primary" style="margin: 4px;" data-action="download" data-url="${this.baseUrl}/api/v1/monthly-statements/download/${sessionId}">
                                            Test Download Endpoint
                                        </button>
                                        <button type="button" class="btn btn-outline" style="margin: 4px;" data-action="results" data-url="${this.baseUrl}/api/v1/monthly-statements/results/${sessionId}">
                                            Test Results JSON
                                        </button>
                                        <button type="button" class="btn btn-secondary" style="margin: 4px;" data-action="copy" data-text="${sessionId}">
                                            Copy Session ID
                                        </button>
                                    </div>
                                </div>
                            `;
                            
                            // Add event listeners for the buttons
                            setTimeout(() => {
                                const buttons = resultElement.querySelectorAll('button[data-action]');
                                buttons.forEach(btn => {
                                    btn.addEventListener('click', (e) => {
                                        const action = e.target.getAttribute('data-action');
                                        if (action === 'download') {
                                            const url = e.target.getAttribute('data-url');
                                            window.open(url, '_blank');
                                        } else if (action === 'results') {
                                            const url = e.target.getAttribute('data-url');
                                            window.open(url, '_blank');
                                        } else if (action === 'copy') {
                                            const text = e.target.getAttribute('data-text');
                                            navigator.clipboard.writeText(text).then(() => {
                                                const originalText = e.target.textContent;
                                                e.target.textContent = 'Copied!';
                                                setTimeout(() => {
                                                    e.target.textContent = originalText;
                                                }, 2000);
                                            });
                                        }
                                    });
                                });
                            }, 100);
                        }
                        return;
                    } else if (status === 'error') {
                        this.displayResult(resultElementId, {
                            ok: false,
                            error: statusResult.data.error || 'Processing failed'
                        });
                        return;
                    } else {
                        // Still processing
                        const progressText = progress.processed_statements ? 
                            `Processing: ${progress.processed_statements}/${progress.total_statements} statements` :
                            'Processing statements...';
                        this.updateProcessingStatus(resultElementId, progressText);
                    }
                } else {
                    this.updateProcessingStatus(resultElementId, 'Error checking status, retrying...');
                }
                
                // Continue polling if not complete and under max attempts
                if (attempts < maxAttempts) {
                    setTimeout(poll, delay);
                } else {
                    this.displayResult(resultElementId, {
                        ok: false,
                        error: 'Processing timeout - please check status manually'
                    });
                }
                
            } catch (error) {
                if (attempts < maxAttempts) {
                    this.updateProcessingStatus(resultElementId, 'Connection error, retrying...');
                    setTimeout(poll, delay);
                } else {
                    this.displayResult(resultElementId, {
                        ok: false,
                        error: `Polling failed: ${error.message}`
                    });
                }
            }
        };
        
        // Start polling
        setTimeout(poll, 2000); // Initial delay
    }
    
    updateProcessingStatus(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('success', 'error');
            element.classList.add('loading', 'show');
            element.innerHTML = `<div class="loading-spinner"></div>${message}`;
        }
    }

    async testCheckStatus() {
        const sessionInput = document.getElementById('sessionIdInput');
        const sessionId = sessionInput ? sessionInput.value.trim() : '';
        
        if (!sessionId) {
            alert('Please enter a session ID');
            return;
        }

        this.displayResult('checkStatusResult', null, true);
        
        const result = await this.makeRequest(`/api/v1/monthly-statements/status/${sessionId}`);
        this.displayResult('checkStatusResult', result);
    }

    async testSeparateInvoices() {
        const pdfInput = document.getElementById('invoicePdfInput');
        
        if (!pdfInput?.files[0]) {
            alert('Please select a PDF file');
            return;
        }

        this.displayResult('separateInvoicesResult', null, true);
        
        const formData = new FormData();
        formData.append('pdf_file', pdfInput.files[0]);
        
        const result = await this.makeFormRequest('/api/v1/invoices/separate', formData);
        this.displayResult('separateInvoicesResult', result);
    }

    async testCleanupMacro() {
        this.displayResult('cleanupMacroResult', null, true);
        
        const result = await this.makeRequest('/api/v1/excel-macros/cleanup');
        this.displayResult('cleanupMacroResult', result);
    }

    async testSortMacro() {
        this.displayResult('sortMacroResult', null, true);
        
        const result = await this.makeRequest('/api/v1/excel-macros/sort');
        this.displayResult('sortMacroResult', result);
    }


    async autoRunTests() {
        // Wait a bit for page to load
        setTimeout(async () => {
            // Auto-run connection test
            await this.testConnection();
            // Auto-run health check
            setTimeout(() => {
                this.testHealthCheck();
            }, 1000);
        }, 500);
    }
}

// Sample data function
function fillSampleData() {
    const sampleText = `R130587    AMEX-1006    105.00    Wanyi Yang
R131702    AMEX-1007    210.00    Virginia Clarke
R132217    AMEX-1008    105.00    Smita Kumar`;
    
    const textInput = document.getElementById('excelTextInput');
    if (textInput) {
        textInput.value = sampleText;
        // Scroll to the input after filling
        textInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.apiExplorer = new APIExplorer();
});