// AlaeAutomates API Explorer JavaScript
class APIExplorer {
    constructor() {
        this.baseUrl = window.location.origin;
        console.log(`[APIExplorer] Initialized with base URL: ${this.baseUrl}`);
        console.log(`[APIExplorer] Window location:`, window.location);
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupTabNavigation();
        this.setupEndpointToggles();
        this.loadBaseUrl();
    }

    setupEventListeners() {
        // Base URL input
        document.getElementById('baseUrl').addEventListener('change', (e) => {
            this.baseUrl = e.target.value.replace(/\/$/, ''); // Remove trailing slash
            localStorage.setItem('apiBaseUrl', this.baseUrl);
        });

        // Test connection button
        document.getElementById('testConnection').addEventListener('click', () => {
            this.testConnection();
        });

        // Health check button
        document.getElementById('healthCheck').addEventListener('click', () => {
            this.testHealthCheck();
        });
    }

    setupTabNavigation() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const sections = document.querySelectorAll('.api-section');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove active class from all tabs and sections
                tabBtns.forEach(b => b.classList.remove('active'));
                sections.forEach(s => s.classList.remove('active'));

                // Add active class to clicked tab
                btn.classList.add('active');

                // Show corresponding section
                const sectionId = btn.getAttribute('data-section');
                const section = document.getElementById(sectionId);
                if (section) {
                    section.classList.add('active');
                }
            });
        });
    }

    setupEndpointToggles() {
        const toggleBtns = document.querySelectorAll('.btn-toggle');
        
        toggleBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetId = btn.getAttribute('data-target');
                const content = document.getElementById(targetId);
                
                if (content) {
                    content.classList.toggle('active');
                    btn.classList.toggle('active');
                }
            });
        });
    }

    loadBaseUrl() {
        const savedUrl = localStorage.getItem('apiBaseUrl');
        if (savedUrl) {
            this.baseUrl = savedUrl;
            document.getElementById('baseUrl').value = savedUrl;
        }
    }

    async makeRequest(url, options = {}) {
        const fullUrl = `${this.baseUrl}${url}`;
        console.log(`[APIExplorer] Making request to: ${fullUrl}`);
        console.log(`[APIExplorer] Base URL: ${this.baseUrl}`);
        console.log(`[APIExplorer] Request options:`, options);
        
        try {
            const response = await fetch(fullUrl, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            console.log(`[APIExplorer] Response status: ${response.status}`);
            console.log(`[APIExplorer] Response ok: ${response.ok}`);

            const data = await response.json();
            console.log(`[APIExplorer] Response data:`, data);
            
            return {
                ok: response.ok,
                status: response.status,
                data: data
            };
        } catch (error) {
            console.error(`[APIExplorer] Request failed:`, error);
            console.error(`[APIExplorer] Error message: ${error.message}`);
            console.error(`[APIExplorer] Error stack:`, error.stack);
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

        element.classList.remove('success', 'error', 'loading');
        
        if (isLoading) {
            element.classList.add('loading', 'show');
            element.innerHTML = '<div class="loading-spinner"></div>Loading...';
            return;
        }

        if (result.ok) {
            element.classList.add('success', 'show');
            element.textContent = JSON.stringify(result.data, null, 2);
        } else {
            element.classList.add('error', 'show');
            const errorMsg = result.error || (result.data && result.data.error) || 'Request failed';
            element.textContent = `Error ${result.status}: ${errorMsg}`;
        }
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
                button.innerHTML = '<i class="fas fa-check"></i>Connected';
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 2000);
            } else {
                this.showConnectionStatus(false);
                button.innerHTML = '<i class="fas fa-times"></i>Failed';
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 2000);
            }
        } catch (error) {
            this.showConnectionStatus(false);
            button.innerHTML = '<i class="fas fa-times"></i>Failed';
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 2000);
        }
    }

    showConnectionStatus(connected) {
        let statusEl = document.querySelector('.connection-status');
        
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.className = 'connection-status';
            document.querySelector('.header-info').appendChild(statusEl);
        }

        if (connected) {
            statusEl.className = 'connection-status connected';
            statusEl.innerHTML = '<i class="fas fa-circle"></i>Connected';
        } else {
            statusEl.className = 'connection-status disconnected';
            statusEl.innerHTML = '<i class="fas fa-circle"></i>Disconnected';
        }
    }

    async testHealthCheck() {
        this.displayResult('healthResult', null, true);
        const result = await this.makeRequest('/');
        this.displayResult('healthResult', result);
    }
}

// API Testing Functions
async function testParseExcelText() {
    const apiExplorer = window.apiExplorer;
    const excelText = document.getElementById('excelTextInput').value.trim();
    
    if (!excelText) {
        alert('Please enter Excel text data');
        return;
    }

    apiExplorer.displayResult('parseExcelTextResult', null, true);
    
    const result = await apiExplorer.makeRequest('/api/v1/cc-batch/parse-excel-text', {
        method: 'POST',
        body: JSON.stringify({ excel_text: excelText })
    });
    
    apiExplorer.displayResult('parseExcelTextResult', result);
}

async function testProcessExcel() {
    const apiExplorer = window.apiExplorer;
    const fileInput = document.getElementById('excelFileInput');
    
    if (!fileInput.files[0]) {
        alert('Please select an Excel file');
        return;
    }

    apiExplorer.displayResult('processExcelResult', null, true);
    
    const formData = new FormData();
    formData.append('excel_file', fileInput.files[0]);
    
    const result = await apiExplorer.makeFormRequest('/api/v1/cc-batch/process', formData);
    apiExplorer.displayResult('processExcelResult', result);
}

async function testDownloadCode() {
    const apiExplorer = window.apiExplorer;
    const jsCode = document.getElementById('jsCodeInput').value.trim();
    
    if (!jsCode) {
        alert('Please enter JavaScript code');
        return;
    }

    apiExplorer.displayResult('downloadCodeResult', null, true);
    
    try {
        const fullUrl = `${apiExplorer.baseUrl}/api/v1/cc-batch/download-code`;
        const response = await fetch(fullUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: jsCode })
        });

        if (response.ok) {
            // Handle file download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `automation_${Date.now()}.js`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            apiExplorer.displayResult('downloadCodeResult', {
                ok: true,
                data: { message: 'File downloaded successfully' }
            });
        } else {
            const errorData = await response.json();
            apiExplorer.displayResult('downloadCodeResult', {
                ok: false,
                status: response.status,
                data: errorData
            });
        }
    } catch (error) {
        apiExplorer.displayResult('downloadCodeResult', {
            ok: false,
            error: error.message
        });
    }
}

async function testProcessStatements() {
    const apiExplorer = window.apiExplorer;
    const pdfFile = document.getElementById('pdfFileInput').files[0];
    const excelFile = document.getElementById('excelStatementsInput').files[0];
    
    if (!pdfFile || !excelFile) {
        alert('Please select both PDF and Excel files');
        return;
    }

    apiExplorer.displayResult('processStatementsResult', null, true);
    
    const formData = new FormData();
    formData.append('pdf_file', pdfFile);
    formData.append('excel_file', excelFile);
    
    const result = await apiExplorer.makeFormRequest('/api/v1/monthly-statements/process', formData);
    apiExplorer.displayResult('processStatementsResult', result);
}

async function testCheckStatus() {
    const apiExplorer = window.apiExplorer;
    const sessionId = document.getElementById('sessionIdInput').value.trim();
    
    if (!sessionId) {
        alert('Please enter a session ID');
        return;
    }

    apiExplorer.displayResult('checkStatusResult', null, true);
    
    const result = await apiExplorer.makeRequest(`/api/v1/monthly-statements/status/${sessionId}`);
    apiExplorer.displayResult('checkStatusResult', result);
}

async function testSeparateInvoices() {
    const apiExplorer = window.apiExplorer;
    const pdfFile = document.getElementById('invoicePdfInput').files[0];
    
    if (!pdfFile) {
        alert('Please select a PDF file');
        return;
    }

    apiExplorer.displayResult('separateInvoicesResult', null, true);
    
    const formData = new FormData();
    formData.append('pdf_file', pdfFile);
    
    const result = await apiExplorer.makeFormRequest('/api/v1/invoices/separate', formData);
    apiExplorer.displayResult('separateInvoicesResult', result);
}

async function testCleanupMacro() {
    const apiExplorer = window.apiExplorer;
    
    apiExplorer.displayResult('cleanupMacroResult', null, true);
    
    const result = await apiExplorer.makeRequest('/api/v1/excel-macros/cleanup');
    apiExplorer.displayResult('cleanupMacroResult', result);
}

async function testSortMacro() {
    const apiExplorer = window.apiExplorer;
    
    apiExplorer.displayResult('sortMacroResult', null, true);
    
    const result = await apiExplorer.makeRequest('/api/v1/excel-macros/sort');
    apiExplorer.displayResult('sortMacroResult', result);
}

// Auto-fill sample data
function fillSampleData() {
    const sampleExcelText = `R130587    AMEX-1006    105.00    Wanyi Yang
R131702    AMEX-1007    210.00    Virginia Clarke
R132217    AMEX-1008    105.00    Smita Kumar`;
    
    document.getElementById('excelTextInput').value = sampleExcelText;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.apiExplorer = new APIExplorer();
    
    // Add sample data button
    const sampleBtn = document.createElement('button');
    sampleBtn.textContent = '📝 Fill Sample Data';
    sampleBtn.className = 'btn-test';
    sampleBtn.style.marginLeft = '0.5rem';
    sampleBtn.onclick = fillSampleData;
    
    const excelTextInput = document.getElementById('excelTextInput');
    if (excelTextInput && excelTextInput.parentNode) {
        excelTextInput.parentNode.appendChild(sampleBtn);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to test the currently visible endpoint
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        
        const activeSection = document.querySelector('.api-section.active');
        if (activeSection) {
            const firstTestBtn = activeSection.querySelector('.btn-test');
            if (firstTestBtn) {
                firstTestBtn.click();
            }
        }
    }
    
    // Ctrl/Cmd + K to focus on base URL input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('baseUrl').focus();
    }
});

// Add copy functionality to code blocks
document.addEventListener('click', (e) => {
    if (e.target.closest('.code-block')) {
        const codeBlock = e.target.closest('.code-block');
        const code = codeBlock.querySelector('code');
        if (code) {
            navigator.clipboard.writeText(code.textContent).then(() => {
                // Show temporary feedback
                const originalBg = codeBlock.style.background;
                codeBlock.style.background = '#dcfce7';
                setTimeout(() => {
                    codeBlock.style.background = originalBg;
                }, 200);
            });
        }
    }
});

// Add tooltips
function createTooltip(element, text) {
    element.title = text;
    element.style.cursor = 'help';
}

// Initialize tooltips after DOM load
document.addEventListener('DOMContentLoaded', () => {
    // Add tooltips to method badges
    document.querySelectorAll('.method.get').forEach(el => {
        createTooltip(el, 'GET request - Retrieves data without side effects');
    });
    
    document.querySelectorAll('.method.post').forEach(el => {
        createTooltip(el, 'POST request - Sends data to create or process resources');
    });
    
    // Add click-to-copy feedback to code blocks
    document.querySelectorAll('.code-block').forEach(block => {
        const copyHint = document.createElement('div');
        copyHint.textContent = 'Click to copy';
        copyHint.style.cssText = `
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            opacity: 0;
            transition: opacity 0.2s;
        `;
        
        block.style.position = 'relative';
        block.appendChild(copyHint);
        
        block.addEventListener('mouseenter', () => {
            copyHint.style.opacity = '1';
        });
        
        block.addEventListener('mouseleave', () => {
            copyHint.style.opacity = '0';
        });
    });
});