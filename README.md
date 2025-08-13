# AlaeAutomates 2.0 Backend API

**100% Free Railway Deployment** | **Complete REST API** | **Frontend Ready**

This is the complete backend API for AlaeAutomates 2.0, extracted as a standalone service that can be deployed to Railway for free and connected to any frontend framework.

## 🚀 Quick Start

### 1. Deploy to Railway (100% Free)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/python-flask)

**Step-by-step Railway deployment:**

1. **Create Railway Account**: Go to [railway.app](https://railway.app) and sign up with GitHub
2. **Create New Project**: Click "New Project" → "Deploy from GitHub repo"
3. **Connect Repository**: 
   - Upload this backend code to your GitHub repository
   - Connect the repository to Railway
4. **Auto Deploy**: Railway will automatically:
   - Detect it's a Python/Flask app
   - Install dependencies from `requirements.txt`
   - Start the server using the `Procfile`
   - Provide a free subdomain (e.g., `your-app.railway.app`)

**Railway Free Tier Limits:**
- ✅ 500 hours/month (plenty for development)
- ✅ 1GB RAM
- ✅ 1GB Storage
- ✅ Custom domain support
- ✅ Automatic SSL certificates

### 2. Local Development

```bash
# Clone the repository
git clone <your-repo-url>
cd BackEndAPIs

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

Server will start at `http://localhost:5000`

## 📡 API Endpoints

### Base URL
```
Production: https://your-app.railway.app
Local: http://localhost:5000
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/v1/help` | API information |
| `GET` | `/api/v1/docs` | Complete documentation |

## 💻 Frontend Integration

### React Example

```jsx
// React component for monthly statements processing
import React, { useState } from 'react';

const API_BASE_URL = 'https://your-app.railway.app'; // Replace with your Railway URL

function MonthlyStatementsUpload() {
  const [files, setFiles] = useState({ pdf: null, excel: null });
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState('idle');

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append('pdf_file', files.pdf);
    formData.append('excel_file', files.excel);

    try {
      setStatus('uploading');
      const response = await fetch(`${API_BASE_URL}/api/v1/monthly-statements/process`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      if (result.success) {
        setSessionId(result.session_id);
        setStatus('processing');
        checkStatus(result.session_id);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setStatus('error');
    }
  };

  const checkStatus = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/monthly-statements/status/${sessionId}`);
      const status = await response.json();
      
      if (status.status === 'completed') {
        if (status.requires_questions) {
          setStatus('questions');
        } else {
          setStatus('ready');
        }
      } else if (status.status === 'processing') {
        // Check again in 2 seconds
        setTimeout(() => checkStatus(sessionId), 2000);
      }
    } catch (error) {
      console.error('Status check failed:', error);
    }
  };

  const downloadResults = () => {
    window.open(`${API_BASE_URL}/api/v1/monthly-statements/download/${sessionId}`);
  };

  return (
    <div>
      <h2>Monthly Statements Processing</h2>
      
      <div>
        <input 
          type="file" 
          accept=".pdf" 
          onChange={(e) => setFiles({...files, pdf: e.target.files[0]})} 
        />
        <input 
          type="file" 
          accept=".xlsx,.xls" 
          onChange={(e) => setFiles({...files, excel: e.target.files[0]})} 
        />
        <button onClick={handleUpload} disabled={!files.pdf || !files.excel}>
          Process Files
        </button>
      </div>

      {status === 'processing' && <p>Processing files...</p>}
      {status === 'questions' && <p>Manual review required - check questions endpoint</p>}
      {status === 'ready' && (
        <button onClick={downloadResults}>Download Results</button>
      )}
    </div>
  );
}

export default MonthlyStatementsUpload;
```

### Vue.js Example

```vue
<template>
  <div class="invoice-separator">
    <h2>Invoice Separator</h2>
    
    <input 
      type="file" 
      accept=".pdf" 
      @change="handleFileSelect" 
      ref="fileInput"
    />
    
    <button @click="separateInvoices" :disabled="!pdfFile">
      Separate Invoices
    </button>
    
    <div v-if="result">
      <p>{{ result.message }}</p>
      <a :href="result.download_url" download>Download Separated Invoices</a>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      pdfFile: null,
      result: null,
      loading: false
    };
  },
  methods: {
    handleFileSelect(event) {
      this.pdfFile = event.target.files[0];
    },
    
    async separateInvoices() {
      if (!this.pdfFile) return;
      
      const formData = new FormData();
      formData.append('pdf_file', this.pdfFile);
      
      try {
        this.loading = true;
        const response = await fetch(`${process.env.VUE_APP_API_URL}/api/v1/invoices/separate`, {
          method: 'POST',
          body: formData
        });
        
        const result = await response.json();
        if (result.success) {
          this.result = result;
        }
      } catch (error) {
        console.error('Invoice separation failed:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

### JavaScript/Vanilla Example

```javascript
// Vanilla JavaScript for Excel macro retrieval
class ExcelMacrosAPI {
  constructor(apiBaseUrl) {
    this.apiBaseUrl = apiBaseUrl;
  }

  async getCleanupMacro() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/excel-macros/cleanup`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to get cleanup macro:', error);
      return null;
    }
  }

  async getSortMacro() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/excel-macros/sort`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to get sort macro:', error);
      return null;
    }
  }

  displayMacro(macroData, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
      <h3>${macroData.macro_name}</h3>
      <pre><code>${macroData.macro_code}</code></pre>
      <div>
        <h4>Instructions:</h4>
        <ol>
          ${macroData.instructions.map(instruction => `<li>${instruction}</li>`).join('')}
        </ol>
      </div>
      <div>
        <h4>Features:</h4>
        <ul>
          ${macroData.features.map(feature => `<li>${feature}</li>`).join('')}
        </ul>
      </div>
    `;
  }
}

// Usage
const api = new ExcelMacrosAPI('https://your-app.railway.app');

document.getElementById('getCleanupMacro').addEventListener('click', async () => {
  const macro = await api.getCleanupMacro();
  if (macro) {
    api.displayMacro(macro, 'macroDisplay');
  }
});
```

### Python Client Example

```python
import requests
import json

class AlaeAutomatesClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
    
    def process_monthly_statements(self, pdf_path, excel_path):
        """Process monthly statements"""
        url = f"{self.base_url}/api/v1/monthly-statements/process"
        
        with open(pdf_path, 'rb') as pdf_file, open(excel_path, 'rb') as excel_file:
            files = {
                'pdf_file': pdf_file,
                'excel_file': excel_file
            }
            
            response = requests.post(url, files=files)
            return response.json()
    
    def check_status(self, session_id):
        """Check processing status"""
        url = f"{self.base_url}/api/v1/monthly-statements/status/{session_id}"
        response = requests.get(url)
        return response.json()
    
    def separate_invoices(self, pdf_path):
        """Separate invoices from PDF"""
        url = f"{self.base_url}/api/v1/invoices/separate"
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {'pdf_file': pdf_file}
            response = requests.post(url, files=files)
            return response.json()
    
    def process_cc_batch(self, excel_path):
        """Process credit card batch Excel"""
        url = f"{self.base_url}/api/v1/cc-batch/process"
        
        with open(excel_path, 'rb') as excel_file:
            files = {'excel_file': excel_file}
            response = requests.post(url, files=files)
            return response.json()

# Usage example
client = AlaeAutomatesClient('https://your-app.railway.app')

# Process monthly statements
result = client.process_monthly_statements('statements.pdf', 'companies.xlsx')
print(f"Session ID: {result['session_id']}")

# Check status
status = client.check_status(result['session_id'])
print(f"Status: {status['status']}")
```

## 🔧 API Features

### 1. Monthly Statements Processing

**Upload and process PDF statements with Excel company lists**

```javascript
// Start processing
const formData = new FormData();
formData.append('pdf_file', pdfFile);
formData.append('excel_file', excelFile);

const response = await fetch('/api/v1/monthly-statements/process', {
  method: 'POST',
  body: formData
});

const { session_id } = await response.json();

// Check status
const statusResponse = await fetch(`/api/v1/monthly-statements/status/${session_id}`);
const status = await statusResponse.json();

// Handle questions if needed
if (status.requires_questions) {
  const questionsResponse = await fetch(`/api/v1/monthly-statements/questions/${session_id}`);
  const question = await questionsResponse.json();
  
  // Answer question
  await fetch(`/api/v1/monthly-statements/questions/${session_id}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ response: 'y' }) // y, n, s, or p
  });
}

// Download results
window.open(`/api/v1/monthly-statements/download/${session_id}`);
```

### 2. Invoice Separation

**Split multi-invoice PDFs into separate files**

```javascript
const formData = new FormData();
formData.append('pdf_file', pdfFile);

const response = await fetch('/api/v1/invoices/separate', {
  method: 'POST',
  body: formData
});

const result = await response.json();
// result.download_url contains the ZIP download link
```

### 3. Excel Macros

**Get VBA macro code for Excel automation**

```javascript
// Get cleanup macro
const cleanupResponse = await fetch('/api/v1/excel-macros/cleanup');
const cleanupMacro = await cleanupResponse.json();

// Get sort macro  
const sortResponse = await fetch('/api/v1/excel-macros/sort');
const sortMacro = await sortResponse.json();

// Both return: { macro_name, macro_code, instructions, features }
```

### 4. Credit Card Batch Processing

**Process Excel files and generate robust JavaScript automation**

```javascript
// Option 1: Upload Excel file
const formData = new FormData();
formData.append('excel_file', excelFile);

const response = await fetch('/api/v1/cc-batch/process', {
  method: 'POST',
  body: formData
});

// Option 2: Parse text data (like frontend)
const textResponse = await fetch('/api/v1/cc-batch/parse-excel-text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    excel_text: "R130587    AMEX-1006    105.00    Wanyi Yang\nR131702    AMEX-1007    210.00    Virginia Clarke"
  })
});

const result = await response.json();
// result.javascript_code contains the robust automation script

// Usage: Paste code in browser console, then click green triangle on each page
// Features: Legacy Edge compatible, visibility checks, record skipping prevention

// Download the JavaScript file
await fetch('/api/v1/cc-batch/download-code', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ code: result.javascript_code })
});
```

## 🌐 CORS Configuration

The API is configured with CORS enabled for all origins by default. For production, update the CORS settings:

```python
# In app.py, modify:
CORS(app, origins=["https://your-frontend-domain.com"])
```

## 🔒 Security Features

- ✅ File type validation using magic numbers
- ✅ Filename sanitization
- ✅ File size limits (50MB max)
- ✅ Rate limiting (1000/day, 100/hour, 20/minute)
- ✅ Secure file permissions
- ✅ Automatic cleanup of temporary files
- ✅ Input sanitization
- ✅ Security headers

## 📊 Rate Limits

| Limit | Value |
|-------|-------|
| Per Day | 1,000 requests |
| Per Hour | 100 requests |
| Per Minute | 20 requests |

## 🎯 Frontend Framework Examples

### Next.js Integration

```javascript
// pages/api/proxy/[...path].js - API proxy to avoid CORS
export default async function handler(req, res) {
  const { path } = req.query;
  const apiUrl = `${process.env.BACKEND_API_URL}/${path.join('/')}`;
  
  const response = await fetch(apiUrl, {
    method: req.method,
    headers: req.headers,
    body: req.method !== 'GET' ? req.body : undefined
  });
  
  const data = await response.json();
  res.status(response.status).json(data);
}
```

### Angular Service

```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AlaeAutomatesService {
  private apiUrl = 'https://your-app.railway.app/api/v1';

  constructor(private http: HttpClient) {}

  processMonthlyStatements(pdfFile: File, excelFile: File): Observable<any> {
    const formData = new FormData();
    formData.append('pdf_file', pdfFile);
    formData.append('excel_file', excelFile);
    
    return this.http.post(`${this.apiUrl}/monthly-statements/process`, formData);
  }

  checkStatus(sessionId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/monthly-statements/status/${sessionId}`);
  }

  separateInvoices(pdfFile: File): Observable<any> {
    const formData = new FormData();
    formData.append('pdf_file', pdfFile);
    
    return this.http.post(`${this.apiUrl}/invoices/separate`, formData);
  }
}
```

### Svelte Integration

```svelte
<script>
  import { onMount } from 'svelte';
  
  let pdfFile;
  let excelFile;
  let processing = false;
  let result = null;
  
  const API_BASE_URL = 'https://your-app.railway.app';
  
  async function processFiles() {
    if (!pdfFile || !excelFile) return;
    
    const formData = new FormData();
    formData.append('pdf_file', pdfFile);
    formData.append('excel_file', excelFile);
    
    try {
      processing = true;
      const response = await fetch(`${API_BASE_URL}/api/v1/monthly-statements/process`, {
        method: 'POST',
        body: formData
      });
      
      result = await response.json();
    } catch (error) {
      console.error('Processing failed:', error);
    } finally {
      processing = false;
    }
  }
</script>

<main>
  <h1>Monthly Statements Processor</h1>
  
  <input type="file" accept=".pdf" bind:files={pdfFile} />
  <input type="file" accept=".xlsx,.xls" bind:files={excelFile} />
  
  <button on:click={processFiles} disabled={processing}>
    {processing ? 'Processing...' : 'Process Files'}
  </button>
  
  {#if result}
    <pre>{JSON.stringify(result, null, 2)}</pre>
  {/if}
</main>
```

## 🚀 Deployment Tips

### Environment Variables

Set these in Railway dashboard:

```
SECRET_KEY=your-secret-key-generate-new-one
FLASK_ENV=production
```

### Custom Domain

1. Go to Railway project settings
2. Click "Domains" 
3. Add your custom domain
4. Update DNS records as shown
5. SSL certificate is automatically generated

### Monitoring

Railway provides built-in monitoring:
- View logs in real-time
- Monitor resource usage
- Set up alerts
- Track deployments

## 🔍 Error Handling

The API returns consistent error responses:

```json
{
  "error": "Description of what went wrong"
}
```

HTTP status codes:
- `200` - Success
- `400` - Bad request (missing/invalid parameters)
- `404` - Resource not found
- `422` - File validation failed
- `500` - Internal server error

## 📱 Mobile App Integration

### React Native

```javascript
import DocumentPicker from 'react-native-document-picker';

const pickAndProcessFile = async () => {
  try {
    const pdfResult = await DocumentPicker.pickSingle({
      type: DocumentPicker.types.pdf,
    });
    
    const excelResult = await DocumentPicker.pickSingle({
      type: DocumentPicker.types.allFiles,
    });

    const formData = new FormData();
    formData.append('pdf_file', {
      uri: pdfResult.uri,
      name: pdfResult.name,
      type: pdfResult.type,
    });
    formData.append('excel_file', {
      uri: excelResult.uri,
      name: excelResult.name,
      type: excelResult.type,
    });

    const response = await fetch(
      'https://your-app.railway.app/api/v1/monthly-statements/process',
      {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    const result = await response.json();
    console.log('Processing started:', result.session_id);
  } catch (error) {
    console.error('Error:', error);
  }
};
```

### Flutter

```dart
import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';

class AlaeAutomatesService {
  final Dio _dio = Dio();
  final String baseUrl = 'https://your-app.railway.app/api/v1';

  Future<Map<String, dynamic>> processMonthlyStatements() async {
    try {
      // Pick files
      FilePickerResult? pdfResult = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
      );
      
      FilePickerResult? excelResult = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['xlsx', 'xls'],
      );

      if (pdfResult != null && excelResult != null) {
        FormData formData = FormData.fromMap({
          'pdf_file': await MultipartFile.fromFile(
            pdfResult.files.single.path!,
            filename: pdfResult.files.single.name,
          ),
          'excel_file': await MultipartFile.fromFile(
            excelResult.files.single.path!,
            filename: excelResult.files.single.name,
          ),
        });

        Response response = await _dio.post(
          '$baseUrl/monthly-statements/process',
          data: formData,
        );

        return response.data;
      }
    } catch (error) {
      print('Error processing files: $error');
    }
    
    return {};
  }
}
```

## 🎉 Success! Your Backend is Ready

You now have a complete, production-ready backend API that can be deployed to Railway for free and connected to any frontend framework. The API maintains all the original functionality with O(n) complexity and enterprise-level security.

**Next Steps:**
1. Deploy to Railway using the button above
2. Update your frontend to use the Railway URL
3. Build amazing user interfaces on top of this solid API foundation!

## 🆘 Support

If you encounter any issues:
1. Check the Railway logs for error details
2. Ensure all required files are uploaded correctly
3. Verify file size limits (50MB max)
4. Test endpoints individually using the examples above

The backend handles all the complex document processing, so you can focus on creating great user experiences!