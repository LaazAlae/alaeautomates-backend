###############################################################################
# CREDIT CARD BATCH PROCESSING API MODULE
# RESTful endpoints for credit card automation
###############################################################################

from flask import Blueprint, request, jsonify, send_file
import pandas as pd
import re
import os
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename

from app.utils.security import (
    secure_error_response,
    log_security_event
)

cc_batch_api = Blueprint('cc_batch_api', __name__)

def process_excel_data(df):
    """Process Excel data for credit card batch automation - O(n) complexity"""
    processed_data = []
    
    for index, row in df.iterrows():
        try:
            # Skip empty rows
            if row.isna().all():
                continue
                
            # Extract data from correct columns (based on original VBA logic)
            invoice_number = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""  # Column B
            customer = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""         # Column E  
            card_type = str(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) else ""        # Column F
            card_number = str(row.iloc[6]) if len(row) > 6 and pd.notna(row.iloc[6]) else ""      # Column G
            settlement = str(row.iloc[7]) if len(row) > 7 and pd.notna(row.iloc[7]) else ""       # Column H
            
            # Skip if any critical field is missing
            if not settlement or settlement == 'nan':
                continue
                
            # Skip refunds (amounts in parentheses)
            if '(' in settlement and ')' in settlement:
                continue
            
            # Process customer name (lastname, firstname -> firstname lastname)
            if ',' in customer:
                parts = customer.split(',', 1)
                if len(parts) >= 2:
                    last_name = parts[0].strip()
                    first_name = parts[1].strip()
                    customer = f"{first_name} {last_name}"
            
            # Special case for BILL.COM
            if 'BILL .COM' in customer.upper():
                customer = 'BILL.COM'
            
            # Process card payment method
            payment_method = ""
            if card_type and card_number:
                # Map card type letters to full names
                if card_type.upper().startswith('A'):
                    payment_method = "AMEX-"
                elif card_type.upper().startswith('V'):
                    payment_method = "VISA-"
                elif card_type.upper().startswith('M'):
                    payment_method = "MC-"
                elif card_type.upper().startswith('D'):
                    payment_method = "DISC-"
                
                # Extract last 4 digits
                if 'XXXX' in card_number:
                    card_digits = card_number.replace('XXXX', '').strip()
                    if card_digits.isdigit():
                        card_last_four = card_digits.zfill(4)
                        payment_method += card_last_four
                elif card_number.isdigit():
                    card_last_four = card_number[-4:].zfill(4)
                    payment_method += card_last_four
            
            # Process invoice number
            processed_invoice = ""
            if invoice_number and invoice_number != 'nan':
                # Clean multiple invoice numbers (take first)
                if ',' in invoice_number:
                    invoice_number = invoice_number.split(',')[0].strip()
                
                invoice_number = invoice_number.strip().upper()
                
                # Validate invoice format (P or R followed by digits)
                if re.match(r'^[PR]\d+', invoice_number):
                    processed_invoice = invoice_number
                else:
                    processed_invoice = f"Line {index + 1} TBD manually"
            else:
                processed_invoice = f"Line {index + 1} TBD manually"
            
            # Clean settlement amount
            try:
                clean_amount = re.sub(r'[^\d.-]', '', str(settlement))
                settlement_amount = float(clean_amount)
                settlement_formatted = f"{settlement_amount:.2f}"
            except:
                settlement_formatted = "0.00"
            
            # Skip zero amounts
            if float(settlement_formatted) == 0:
                continue
            
            processed_data.append({
                'invoice': processed_invoice,
                'payment_method': payment_method,
                'amount': settlement_formatted,
                'customer': customer.strip()
            })
            
        except Exception as e:
            log_security_event('excel_processing_error', {'line': index + 1, 'error': str(e)})
            continue
    
    return processed_data

def generate_javascript_code(processed_data):
    """Generate robust JavaScript automation code for legacy Edge compatibility"""
    
    data_array_json = "[\n"
    for item in processed_data:
        data_array_json += f"""    {{
        invoiceNumber: "{item['invoice']}",
        cardPaymentMethod: "{item['payment_method']}",
        settlementAmount: "{item['amount']}",
        customer: "{item['customer']}"
    }},
"""
    data_array_json += "]"
    
    js_code = f"""// ROBUST HEADLESS PAYMENT AUTOMATION
// Generated for {len(processed_data)} payment records
// Click the green triangle to execute each step!

// PAYMENT DATA
var PAYMENT_DATA = {data_array_json};

// PAGE DETECTION
function detectPageAndStep() {{
    var url = window.location.href.toLowerCase();
    var bodyText = document.body.textContent || document.body.innerText || '';
    
    if (url.indexOf('receipt_add_invoice.aspx') !== -1) {{
        var amountField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtAmount')[0];
        var customerField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtCheckName')[0];
        var paymentNumberField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtNumber')[0];
        
        if (customerField && customerField.value && customerField.value.trim() !== '') {{
            return {{ page: 'PAYMENT_FORM_PAGE', step: 8 }};
        }} else if (amountField && amountField.value && amountField.value.trim() !== '') {{
            return {{ page: 'PAYMENT_FORM_PAGE', step: 7 }};
        }} else if (paymentNumberField && paymentNumberField.value && paymentNumberField.value.trim() !== '') {{
            return {{ page: 'PAYMENT_FORM_PAGE', step: 6 }};
        }} else {{
            return {{ page: 'PAYMENT_FORM_PAGE', step: 4 }};
        }}
    }} else if (url.indexOf('batch_page.aspx') !== -1) {{
        if (url.indexOf('view=recadd') !== -1) {{
            return {{ page: 'ADD_RECEIPT_PAGE', step: 1 }};
        }} else if (url.indexOf('view=isrch') !== -1) {{
            var invoiceField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtNumber')[0];
            if (invoiceField && invoiceField.value && invoiceField.value.trim() !== '') {{
                return {{ page: 'SEARCH_PAGE', step: 3 }};
            }} else {{
                return {{ page: 'SEARCH_PAGE', step: 2 }};
            }}
        }} else {{
            if (bodyText.indexOf('Add Receipt') !== -1) {{
                return {{ page: 'MAIN_BATCH_PAGE', step: 0 }};
            }}
        }}
    }}
    return {{ page: 'UNKNOWN_PAGE', step: 0 }};
}}

// ROBUST AUTOMATION WITH SAFEGUARDS
function HeadlessAutomation() {{
    var pageInfo = detectPageAndStep();
    this.currentPageState = pageInfo.page;
    this.processingStep = pageInfo.step;
    this.isExecuting = false;  // Lock to prevent double execution
    
    var cookieIndex = this.getCookie('automationIndex');
    if (cookieIndex !== null) {{
        this.currentRecordIndex = parseInt(cookieIndex);
    }} else {{
        this.currentRecordIndex = 0;
    }}
    
    this.currentRecord = PAYMENT_DATA[this.currentRecordIndex];
    
    console.log('═══════════════════════════════════════');
    console.log('🤖 AUTOMATION STATUS');
    console.log('═══════════════════════════════════════');
    console.log('📍 Page: ' + this.currentPageState);
    console.log('📋 Record: ' + (this.currentRecordIndex + 1) + '/' + PAYMENT_DATA.length);
    if (this.currentRecord) {{
        console.log('📝 Processing: ' + this.currentRecord.invoiceNumber + ' - ' + this.currentRecord.customer);
        console.log('💰 Amount: $' + this.currentRecord.settlementAmount);
    }}
    console.log('🔄 Step: ' + this.getStepName(this.processingStep));
    console.log('═══════════════════════════════════════');
}}

HeadlessAutomation.prototype.getStepName = function(step) {{
    var stepNames = [
        'Click Add Receipt',
        'Click By Invoice', 
        'Enter Invoice Number',
        'Click Search',
        'Select Payment Type',
        'Enter Payment Method',
        'Enter Amount',
        'Enter Customer Name',
        'Click Save',
        'Complete'
    ];
    return stepNames[step] || 'Unknown';
}};

HeadlessAutomation.prototype.execute = function() {{
    if (!this.currentRecord) {{
        console.log('✅ ALL RECORDS COMPLETED!');
        return;
    }}
    
    // Prevent double execution
    if (this.isExecuting) {{
        console.log('⚠️ Already executing, please wait...');
        return;
    }}
    
    this.isExecuting = true;
    var self = this;
    
    // Auto-release lock after 15 seconds as failsafe
    setTimeout(function() {{
        self.isExecuting = false;
    }}, 15000);
    
    switch (this.processingStep) {{
        case 0: // Click Add Receipt
            console.log('🔄 Clicking "Add Receipt"...');
            if (this.clickButton('Add Receipt')) {{
                console.log('✓ Done! Page will redirect...');
            }}
            this.isExecuting = false;
            break;
            
        case 1: // Click By Invoice
            console.log('🔄 Clicking "By Invoice"...');
            if (this.clickButton('By Invoice')) {{
                console.log('✓ Done! Page will redirect...');
            }}
            this.isExecuting = false;
            break;
            
        case 2: // Enter Invoice Number
            var cleanInvoice = this.cleanInvoiceNumber(this.currentRecord.invoiceNumber);
            console.log('🔄 Entering invoice: ' + cleanInvoice);
            if (this.fillFieldSafe('ctl00$ContentPlaceHolder1$txtNumber', cleanInvoice)) {{
                console.log('✓ Invoice entered!');
                setTimeout(function() {{
                    console.log('🔄 Clicking "Search"...');
                    if (self.clickButton('Search')) {{
                        console.log('✓ Search clicked! Page will redirect...');
                    }}
                    self.isExecuting = false;
                }}, 1200);
            }} else {{
                console.log('❌ Could not enter invoice number');
                self.isExecuting = false;
            }}
            break;
            
        case 3: // Click Search (if invoice already entered)
            console.log('🔄 Clicking "Search"...');
            if (this.clickButton('Search')) {{
                console.log('✓ Done! Page will redirect to payment form...');
            }}
            this.isExecuting = false;
            break;
            
        case 4: // Payment form - start filling
            console.log('🔄 Starting payment form fill...');
            this.executePaymentFormFill();
            break;
            
        case 5: // If payment method already selected
        case 6: // If amount already entered
        case 7: // If customer already entered
            console.log('🔍 Form partially filled, completing remaining fields...');
            setTimeout(function() {{ 
                self.completeFormSafe(); 
            }}, 800);
            break;
            
        case 8: // Ready to save
            console.log('🔄 Clicking "Save"...');
            if (this.clickButton('Save')) {{
                console.log('✅ Payment saved!');
                setTimeout(function() {{
                    self.nextRecord();
                    console.log('📝 Ready for next record. Navigate to main batch page and click green triangle again.');
                    self.isExecuting = false;
                }}, 2000);
            }} else {{
                this.isExecuting = false;
            }}
            break;
            
        default:
            console.log('❓ Unknown step: ' + this.processingStep);
            this.isExecuting = false;
    }}
}};

HeadlessAutomation.prototype.executePaymentFormFill = function() {{
    var self = this;
    var paymentType = this.determinePaymentType(this.currentRecord.cardPaymentMethod);
    console.log('→ Selecting payment type: ' + paymentType);
    
    if (this.selectDropdownSafe('ctl00$ContentPlaceHolder1$lstType', paymentType)) {{
        setTimeout(function() {{
            console.log('→ Entering payment method: ' + self.currentRecord.cardPaymentMethod);
            if (self.fillFieldSafe('ctl00$ContentPlaceHolder1$txtNumber', self.currentRecord.cardPaymentMethod)) {{
                
                setTimeout(function() {{
                    console.log('→ Entering amount: $' + self.currentRecord.settlementAmount);
                    if (self.fillFieldSafe('ctl00$ContentPlaceHolder1$txtAmount', self.currentRecord.settlementAmount)) {{
                        
                        setTimeout(function() {{
                            console.log('→ Entering customer: ' + self.currentRecord.customer);
                            if (self.fillFieldSafe('ctl00$ContentPlaceHolder1$txtCheckName', self.currentRecord.customer)) {{
                                
                                setTimeout(function() {{
                                    console.log('🔄 Clicking "Save"...');
                                    if (self.clickButton('Save')) {{
                                        console.log('✅ Payment saved!');
                                        
                                        setTimeout(function() {{
                                            self.nextRecord();
                                            console.log('📝 Ready for next record. Navigate to main batch page and click green triangle again.');
                                            self.isExecuting = false;
                                        }}, 2000);
                                    }} else {{
                                        self.isExecuting = false;
                                    }}
                                }}, 1200);
                            }} else {{
                                self.isExecuting = false;
                            }}
                        }}, 800);
                    }} else {{
                        self.isExecuting = false;
                    }}
                }}, 800);
            }} else {{
                self.isExecuting = false;
            }}
        }}, 800);
    }} else {{
        self.isExecuting = false;
    }}
}};

HeadlessAutomation.prototype.completeFormSafe = function() {{
    var self = this;
    var amountField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtAmount')[0];
    var customerField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtCheckName')[0];
    
    if (amountField && this.isFieldVisible(amountField) && !amountField.value) {{
        console.log('→ Entering amount: $' + this.currentRecord.settlementAmount);
        this.fillFieldSafe('ctl00$ContentPlaceHolder1$txtAmount', this.currentRecord.settlementAmount);
    }}
    
    setTimeout(function() {{
        if (customerField && self.isFieldVisible(customerField) && !customerField.value) {{
            console.log('→ Entering customer: ' + self.currentRecord.customer);
            self.fillFieldSafe('ctl00$ContentPlaceHolder1$txtCheckName', self.currentRecord.customer);
        }}
        
        setTimeout(function() {{
            console.log('🔄 Clicking "Save"...');
            if (self.clickButton('Save')) {{
                console.log('✅ Payment saved!');
                setTimeout(function() {{
                    self.nextRecord();
                    console.log('📝 Ready for next record. Navigate to main batch page and click green triangle again.');
                    self.isExecuting = false;
                }}, 2000);
            }} else {{
                self.isExecuting = false;
            }}
        }}, 1200);
    }}, 800);
}};

HeadlessAutomation.prototype.nextRecord = function() {{
    this.currentRecordIndex++;
    this.setCookie('automationIndex', this.currentRecordIndex.toString());
    
    if (this.currentRecordIndex < PAYMENT_DATA.length) {{
        this.currentRecord = PAYMENT_DATA[this.currentRecordIndex];
        console.log('');
        console.log('📋 Next record: ' + this.currentRecord.invoiceNumber);
    }} else {{
        this.currentRecord = null;
        console.log('');
        console.log('🎉 ALL RECORDS COMPLETED!');
    }}
}};

// SAFE UTILITY FUNCTIONS WITH VISIBILITY CHECKS
HeadlessAutomation.prototype.isFieldVisible = function(field) {{
    if (!field) return false;
    
    // Check if field is visible (legacy Edge compatible)
    var style = field.currentStyle || window.getComputedStyle(field);
    return style.display !== 'none' && 
           style.visibility !== 'hidden' && 
           field.offsetWidth > 0 && 
           field.offsetHeight > 0;
}};

HeadlessAutomation.prototype.fillFieldSafe = function(fieldName, value) {{
    var field = document.getElementsByName(fieldName)[0];
    if (field && this.isFieldVisible(field)) {{
        field.value = value;
        
        // Legacy Edge compatible event triggering
        if (field.fireEvent) {{
            field.fireEvent('onchange');
        }} else {{
            var event = document.createEvent('HTMLEvents');
            event.initEvent('change', true, true);
            field.dispatchEvent(event);
        }}
        
        return true;
    }}
    console.log('❌ Field "' + fieldName + '" not found or not visible');
    return false;
}};

HeadlessAutomation.prototype.selectDropdownSafe = function(dropdownName, value) {{
    var dropdown = document.getElementsByName(dropdownName)[0];
    if (dropdown && this.isFieldVisible(dropdown)) {{
        for (var i = 0; i < dropdown.options.length; i++) {{
            if (dropdown.options[i].text.indexOf(value) !== -1) {{
                dropdown.selectedIndex = i;
                dropdown.value = dropdown.options[i].value;
                
                // Legacy Edge compatible event triggering
                if (dropdown.fireEvent) {{
                    dropdown.fireEvent('onchange');
                }} else {{
                    var event = document.createEvent('HTMLEvents');
                    event.initEvent('change', true, true);
                    dropdown.dispatchEvent(event);
                }}
                
                return true;
            }}
        }}
    }}
    console.log('❌ Dropdown "' + dropdownName + '" or option "' + value + '" not found');
    return false;
}};

HeadlessAutomation.prototype.clickButton = function(buttonText) {{
    var buttons = document.getElementsByTagName('input');
    for (var i = 0; i < buttons.length; i++) {{
        if (buttons[i].value === buttonText && 
            (buttons[i].type === 'submit' || buttons[i].type === 'button') &&
            this.isFieldVisible(buttons[i])) {{
            buttons[i].click();
            return true;
        }}
    }}
    console.log('❌ Button "' + buttonText + '" not found or not visible');
    return false;
}};

HeadlessAutomation.prototype.cleanInvoiceNumber = function(invoice) {{
    return invoice.replace(/^[RP]/i, '');
}};

HeadlessAutomation.prototype.determinePaymentType = function(method) {{
    var methodUpper = method.toUpperCase();
    if (methodUpper.indexOf('AMEX') !== -1) return 'AMEX';
    if (methodUpper.indexOf('VISA') !== -1) return 'VISA';
    if (methodUpper.indexOf('MC') !== -1) return 'MasterCard';
    if (methodUpper.indexOf('DISC') !== -1) return 'Discover';
    return 'Check';
}};

HeadlessAutomation.prototype.setCookie = function(name, value) {{
    document.cookie = name + '=' + value + '; path=/';
}};

HeadlessAutomation.prototype.getCookie = function(name) {{
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {{
        var cookie = cookies[i].trim();
        if (cookie.indexOf(name + '=') === 0) {{
            return cookie.substring(name.length + 1);
        }}
    }}
    return null;
}};

// INITIALIZE AND EXECUTE IMMEDIATELY
var auto = new HeadlessAutomation();
auto.execute();

// Create run function for easy re-execution
window.run = function() {{
    auto = new HeadlessAutomation();
    auto.execute();
}};

// Reset function if needed
window.reset = function() {{
    document.cookie = 'automationIndex=0; path=/';
    console.log('🔄 Reset to first record');
}};

console.log('');
console.log('💡 TIP: Click the green triangle to execute | Type reset() to start over');
console.log('🚀 ROBUST: Safeguards prevent record skipping & legacy Edge compatible!');"""
    
    return js_code

@cc_batch_api.route('/process', methods=['POST'])
def process_batch():
    """Process Excel file for credit card batch automation"""
    try:
        if 'excel_file' not in request.files:
            return jsonify({'error': 'excel_file is required'}), 400
        
        excel_file = request.files['excel_file']
        
        if not excel_file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        if not excel_file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400
        
        # Save file temporarily
        temp_dir = tempfile.mkdtemp()
        filename = secure_filename(excel_file.filename)
        temp_path = os.path.join(temp_dir, filename)
        excel_file.save(temp_path)
        
        try:
            # Read and process Excel file
            df = pd.read_excel(temp_path, header=None)
            
            if df.empty:
                return jsonify({'error': 'Excel file is empty'}), 400
            
            processed_data = process_excel_data(df)
            
            if not processed_data:
                return jsonify({'error': 'No valid data found in Excel file'}), 400
            
            # Generate JavaScript code
            js_code = generate_javascript_code(processed_data)
            
            return jsonify({
                'success': True,
                'records_count': len(processed_data),
                'javascript_code': js_code,
                'processed_data': processed_data[:5],  # Preview of first 5 records
                'message': f'Successfully processed {len(processed_data)} credit card records'
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing Excel file: {str(e)}'}), 500
        
        finally:
            # Cleanup
            try:
                os.remove(temp_path)
                os.rmdir(temp_dir)
            except:
                pass
                
    except Exception as e:
        return jsonify({'error': 'File processing failed'}), 500

@cc_batch_api.route('/download-code', methods=['POST'])
def download_code():
    """Download generated JavaScript code as a file"""
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'error': 'JavaScript code is required'}), 400
        
        js_code = data['code']
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cc_batch_automation_{timestamp}.js"
        temp_path = os.path.join(temp_dir, filename)
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(js_code)
        
        return send_file(temp_path, as_attachment=True, 
                        download_name=filename, mimetype='application/javascript')
                        
    except Exception as e:
        return jsonify({'error': 'Code download failed'}), 500

@cc_batch_api.route('/parse-excel-text', methods=['POST'])
def parse_excel_text():
    """Parse Excel data from text input (mimics frontend behavior exactly)"""
    try:
        data = request.get_json()
        if not data or 'excel_text' not in data:
            return jsonify({'error': 'excel_text is required'}), 400
        
        input_text = data['excel_text'].strip()
        
        if not input_text:
            return jsonify({'error': 'Please provide Excel data input'}), 400
        
        # Parse Excel data exactly like the frontend does
        lines = input_text.split('\n')
        records = []
        
        start_index = 0
        if lines and 'invoice' in lines[0].lower():
            start_index = 1
            
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            # Split by tabs or multiple spaces (like frontend)
            parts = re.split(r'\t+|\s{2,}', line)
            
            if len(parts) >= 4:
                records.append({
                    'invoiceNumber': parts[0].strip(),
                    'cardPaymentMethod': parts[1].strip(),
                    'settlementAmount': parts[2].strip(),
                    'customer': parts[3].strip()
                })
        
        if not records:
            return jsonify({'error': 'No valid data records found. Please verify input format.'}), 400
        
        # Generate the exact same JavaScript code as the frontend
        js_code = generate_javascript_code_from_records(records)
        
        return jsonify({
            'success': True,
            'records_count': len(records),
            'javascript_code': js_code,
            'processed_data': records[:10],  # Preview of first 10 records
            'message': f'Successfully generated code for {len(records)} records'
        })
        
    except Exception as e:
        return jsonify({'error': f'Data parsing error: {str(e)}'}), 500

def generate_javascript_code_from_records(records):
    """Generate robust JavaScript code from parsed records (exact frontend match)"""
    # Just call the main function with the same record structure
    converted_records = []
    for record in records:
        converted_records.append({
            'invoice': record['invoiceNumber'],
            'payment_method': record['cardPaymentMethod'], 
            'amount': record['settlementAmount'],
            'customer': record['customer']
        })
    
    return generate_javascript_code(converted_records)
