# Frontend Integration Guide

This guide shows exactly how to connect different frontend frameworks to your AlaeAutomates 2.0 backend API.

## 🔗 Step 1: Get Your API URL

After deploying to Railway, you'll get a URL like:
```
https://your-project-name.railway.app
```

## 📱 React Integration

### Complete Monthly Statements Component

```jsx
import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'https://your-project-name.railway.app';

const MonthlyStatementsProcessor = () => {
  const [files, setFiles] = useState({ pdf: null, excel: null });
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Upload files and start processing
  const handleUpload = async () => {
    if (!files.pdf || !files.excel) {
      setError('Please select both PDF and Excel files');
      return;
    }

    const formData = new FormData();
    formData.append('pdf_file', files.pdf);
    formData.append('excel_file', files.excel);

    try {
      setStatus('uploading');
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/monthly-statements/process`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        setSessionId(result.session_id);
        setStatus('processing');
        checkStatus(result.session_id);
      } else {
        setError(result.error || 'Upload failed');
        setStatus('error');
      }
    } catch (error) {
      setError(`Upload failed: ${error.message}`);
      setStatus('error');
    }
  };

  // Check processing status
  const checkStatus = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/monthly-statements/status/${sessionId}`);
      const statusData = await response.json();
      
      if (statusData.status === 'completed') {
        if (statusData.requires_questions) {
          setStatus('questions');
          getCurrentQuestion(sessionId);
        } else {
          setStatus('ready');
          getResults(sessionId);
        }
      } else if (statusData.status === 'processing') {
        // Check again in 3 seconds
        setTimeout(() => checkStatus(sessionId), 3000);
      } else if (statusData.status === 'error') {
        setError(statusData.error || 'Processing failed');
        setStatus('error');
      }
    } catch (error) {
      setError(`Status check failed: ${error.message}`);
      setStatus('error');
    }
  };

  // Get current question for manual review
  const getCurrentQuestion = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/monthly-statements/questions/${sessionId}`);
      const questionData = await response.json();
      setCurrentQuestion(questionData);
    } catch (error) {
      setError(`Failed to get question: ${error.message}`);
    }
  };

  // Answer a question
  const answerQuestion = async (response) => {
    try {
      const answerResponse = await fetch(`${API_BASE_URL}/api/v1/monthly-statements/questions/${sessionId}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response })
      });

      const result = await answerResponse.json();
      
      if (result.completed) {
        setStatus('creating_results');
        setCurrentQuestion(null);
        // Wait for results to be ready
        setTimeout(() => checkStatus(sessionId), 2000);
      } else {
        setCurrentQuestion(result.question_state);
      }
    } catch (error) {
      setError(`Failed to answer question: ${error.message}`);
    }
  };

  // Get final results
  const getResults = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/monthly-statements/results/${sessionId}`);
      const resultsData = await response.json();
      
      if (response.ok) {
        setResults(resultsData);
      } else if (response.status === 202) {
        // Results not ready, try again
        setTimeout(() => getResults(sessionId), 2000);
      } else {
        setError(resultsData.error || 'Failed to get results');
      }
    } catch (error) {
      setError(`Failed to get results: ${error.message}`);
    }
  };

  // Download results
  const downloadResults = () => {
    window.open(`${API_BASE_URL}/api/v1/monthly-statements/download/${sessionId}`);
  };

  return (
    <div className="monthly-statements-processor">
      <h2>Monthly Statements Processor</h2>
      
      {/* File Upload */}
      {status === 'idle' && (
        <div className="upload-section">
          <div>
            <label>PDF File:</label>
            <input 
              type="file" 
              accept=".pdf" 
              onChange={(e) => setFiles({...files, pdf: e.target.files[0]})} 
            />
          </div>
          <div>
            <label>Excel File:</label>
            <input 
              type="file" 
              accept=".xlsx,.xls" 
              onChange={(e) => setFiles({...files, excel: e.target.files[0]})} 
            />
          </div>
          <button onClick={handleUpload} disabled={!files.pdf || !files.excel}>
            Start Processing
          </button>
        </div>
      )}

      {/* Status Display */}
      {status === 'uploading' && <p>⬆️ Uploading files...</p>}
      {status === 'processing' && <p>⚙️ Processing statements...</p>}
      {status === 'creating_results' && <p>📄 Creating results...</p>}

      {/* Error Display */}
      {error && (
        <div className="error" style={{color: 'red', padding: '10px', border: '1px solid red'}}>
          ❌ {error}
          <button onClick={() => { setError(null); setStatus('idle'); }}>Try Again</button>
        </div>
      )}

      {/* Questions Section */}
      {status === 'questions' && currentQuestion && !currentQuestion.completed && (
        <div className="questions-section" style={{border: '1px solid #ccc', padding: '20px'}}>
          <h3>Manual Review Required</h3>
          <p><strong>Company:</strong> {currentQuestion.company_name}</p>
          <p><strong>Similar to:</strong> {currentQuestion.similar_to}</p>
          <p><strong>Question {currentQuestion.current} of {currentQuestion.total}:</strong></p>
          <p>Should "{currentQuestion.company_name}" be categorized the same as "{currentQuestion.similar_to}"?</p>
          
          <div className="question-buttons">
            <button onClick={() => answerQuestion('y')} className="btn-yes">
              ✅ Yes - Categorize as DNM
            </button>
            <button onClick={() => answerQuestion('n')} className="btn-no">
              ❌ No - Don't categorize as DNM
            </button>
            <button onClick={() => answerQuestion('s')} className="btn-skip">
              ⏭️ Skip all remaining questions
            </button>
            {currentQuestion.can_go_back && (
              <button onClick={() => answerQuestion('p')} className="btn-prev">
                ⬅️ Previous question
              </button>
            )}
          </div>
        </div>
      )}

      {/* Results Section */}
      {status === 'ready' && results && (
        <div className="results-section">
          <h3>✅ Processing Complete!</h3>
          
          <div className="statistics">
            <h4>Statistics:</h4>
            <p>Total Statements: {results.statistics.total_statements}</p>
            <ul>
              {Object.entries(results.statistics.destinations).map(([dest, count]) => (
                <li key={dest}>{dest}: {count} statements</li>
              ))}
            </ul>
          </div>

          <button onClick={downloadResults} className="download-btn">
            📥 Download Results (ZIP)
          </button>
        </div>
      )}
    </div>
  );
};

export default MonthlyStatementsProcessor;
```

## 🎨 Vue.js Integration

### Complete Invoice Separator Component

```vue
<template>
  <div class="invoice-separator">
    <h2>Invoice Separator</h2>
    
    <!-- File Upload -->
    <div v-if="status === 'idle'" class="upload-section">
      <input 
        type="file" 
        accept=".pdf" 
        @change="handleFileSelect" 
        ref="fileInput"
      />
      <button 
        @click="separateInvoices" 
        :disabled="!pdfFile || loading"
        class="process-btn"
      >
        {{ loading ? 'Processing...' : 'Separate Invoices' }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <p>🔄 Separating invoices...</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <p>❌ {{ error }}</p>
      <button @click="reset">Try Again</button>
    </div>

    <!-- Results -->
    <div v-if="result && result.success" class="results">
      <h3>✅ Success!</h3>
      <p>{{ result.message }}</p>
      <p>Found <strong>{{ result.invoice_count }}</strong> invoices</p>
      <a 
        :href="apiBaseUrl + result.download_url" 
        download
        class="download-link"
      >
        📥 Download Separated Invoices
      </a>
    </div>
  </div>
</template>

<script>
export default {
  name: 'InvoiceSeparator',
  data() {
    return {
      apiBaseUrl: 'https://your-project-name.railway.app', // Replace with your URL
      pdfFile: null,
      result: null,
      loading: false,
      error: null,
      status: 'idle'
    };
  },
  methods: {
    handleFileSelect(event) {
      this.pdfFile = event.target.files[0];
      this.error = null;
    },
    
    async separateInvoices() {
      if (!this.pdfFile) {
        this.error = 'Please select a PDF file';
        return;
      }
      
      const formData = new FormData();
      formData.append('pdf_file', this.pdfFile);
      
      try {
        this.loading = true;
        this.error = null;
        this.status = 'processing';
        
        const response = await fetch(`${this.apiBaseUrl}/api/v1/invoices/separate`, {
          method: 'POST',
          body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
          this.result = result;
          this.status = 'completed';
        } else {
          this.error = result.error || 'Processing failed';
          this.status = 'error';
        }
      } catch (error) {
        this.error = `Processing failed: ${error.message}`;
        this.status = 'error';
      } finally {
        this.loading = false;
      }
    },

    reset() {
      this.pdfFile = null;
      this.result = null;
      this.error = null;
      this.loading = false;
      this.status = 'idle';
      this.$refs.fileInput.value = '';
    }
  }
};
</script>

<style scoped>
.invoice-separator {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.upload-section {
  margin: 20px 0;
  padding: 20px;
  border: 2px dashed #ccc;
  border-radius: 8px;
  text-align: center;
}

.process-btn {
  margin: 10px;
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.process-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  margin: 20px 0;
}

.error {
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
}

.results {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
  padding: 20px;
  border-radius: 4px;
  margin: 10px 0;
}

.download-link {
  display: inline-block;
  margin-top: 10px;
  padding: 10px 20px;
  background-color: #28a745;
  color: white;
  text-decoration: none;
  border-radius: 4px;
}
</style>
```

## ⚛️ Next.js Integration

### API Route Proxy (Optional - to avoid CORS)

```javascript
// pages/api/alaeautomates/[...path].js
export default async function handler(req, res) {
  const { path } = req.query;
  const apiUrl = `${process.env.BACKEND_API_URL}/${path.join('/')}`;
  
  try {
    const response = await fetch(apiUrl, {
      method: req.method,
      headers: {
        ...req.headers,
        host: undefined, // Remove host header
      },
      body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined
    });
    
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    res.status(500).json({ error: 'API proxy failed' });
  }
}
```

### Credit Card Batch Component

```jsx
// components/CreditCardBatch.js
import { useState } from 'react';

export default function CreditCardBatch() {
  const [excelFile, setExcelFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-project-name.railway.app';

  const handleFileSelect = (e) => {
    setExcelFile(e.target.files[0]);
    setError(null);
  };

  const processBatch = async () => {
    if (!excelFile) {
      setError('Please select an Excel file');
      return;
    }

    const formData = new FormData();
    formData.append('excel_file', excelFile);

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/api/v1/cc-batch/process`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setResult(data);
      } else {
        setError(data.error || 'Processing failed');
      }
    } catch (error) {
      setError(`Processing failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadCode = async () => {
    if (!result?.javascript_code) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/cc-batch/download-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: result.javascript_code })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cc_batch_automation_${Date.now()}.js`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      setError(`Download failed: ${error.message}`);
    }
  };

  return (
    <div className="credit-card-batch">
      <h2>Credit Card Batch Processing</h2>
      
      <div className="upload-section">
        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={handleFileSelect}
          disabled={loading}
        />
        <button
          onClick={processBatch}
          disabled={!excelFile || loading}
          className="process-btn"
        >
          {loading ? 'Processing...' : 'Generate Automation Code'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {result && (
        <div className="results-section">
          <h3>✅ Processing Complete!</h3>
          <p>Processed {result.records_count} records</p>
          
          <div className="preview-section">
            <h4>Preview (first 5 records):</h4>
            <pre>{JSON.stringify(result.processed_data, null, 2)}</pre>
          </div>

          <div className="code-section">
            <h4>Generated JavaScript Code:</h4>
            <textarea
              value={result.javascript_code}
              readOnly
              rows={10}
              style={{ width: '100%', fontFamily: 'monospace' }}
            />
          </div>

          <button onClick={downloadCode} className="download-btn">
            📥 Download JavaScript File
          </button>
        </div>
      )}

      <style jsx>{`
        .credit-card-batch {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }
        .upload-section {
          margin: 20px 0;
          padding: 20px;
          border: 2px dashed #ccc;
          border-radius: 8px;
          text-align: center;
        }
        .process-btn, .download-btn {
          margin: 10px;
          padding: 10px 20px;
          background-color: #007bff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }
        .process-btn:disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }
        .error-message {
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
          color: #721c24;
          padding: 10px;
          border-radius: 4px;
          margin: 10px 0;
        }
        .results-section {
          margin: 20px 0;
          padding: 20px;
          border: 1px solid #ccc;
          border-radius: 8px;
        }
        .preview-section, .code-section {
          margin: 15px 0;
        }
      `}</style>
    </div>
  );
}
```

## 🚀 Testing Your Integration

### 1. Test API Connection

```javascript
// Quick test to verify your API is working
const testAPI = async () => {
  const API_URL = 'https://your-project-name.railway.app';
  
  try {
    const response = await fetch(`${API_URL}/api/v1/help`);
    const data = await response.json();
    console.log('✅ API is working:', data);
  } catch (error) {
    console.error('❌ API connection failed:', error);
  }
};

testAPI();
```

### 2. Test File Upload

```javascript
// Test with a small file
const testUpload = async () => {
  const formData = new FormData();
  // Add your test files here
  
  try {
    const response = await fetch('https://your-project-name.railway.app/api/v1/invoices/separate', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    console.log('Upload result:', result);
  } catch (error) {
    console.error('Upload failed:', error);
  }
};
```

## 🛠️ Environment Variables

### Frontend (.env.local for Next.js)
```
NEXT_PUBLIC_API_URL=https://your-project-name.railway.app
```

### Backend (Railway Dashboard)
```
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
```

## 🎯 Common Issues & Solutions

### CORS Issues
The backend is configured with CORS enabled for all origins. If you still encounter CORS issues:

1. Use the API proxy method shown in Next.js example
2. Or modify the backend CORS settings:

```python
# In app.py
CORS(app, origins=["https://your-frontend-domain.com"])
```

### File Upload Issues
- Ensure files are under 50MB
- Check file extensions (.pdf, .xlsx, .xls only)
- Verify the FormData is properly constructed

### Rate Limiting
If you hit rate limits during development:
- Implement request queuing in your frontend
- Cache responses when possible
- Contact support for increased limits if needed

## ✅ Checklist for Going Live

- [ ] Backend deployed to Railway
- [ ] Environment variables set
- [ ] Frontend updated with Railway URL  
- [ ] CORS configured properly
- [ ] Error handling implemented
- [ ] File size limits communicated to users
- [ ] Loading states implemented
- [ ] Success/error messages shown

Your frontend is now ready to use all the powerful AlaeAutomates 2.0 features! 🎉