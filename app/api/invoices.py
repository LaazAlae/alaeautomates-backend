###############################################################################
# INVOICES API MODULE
# RESTful endpoints for invoice separation processing
###############################################################################

from flask import Blueprint, request, jsonify, send_file
import os
import re
import zipfile
import tempfile
from werkzeug.utils import secure_filename

# PDF processing with fallbacks
try:
    from pypdf import PdfReader, PdfWriter
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from app.utils.security import (
    validate_filename,
    validate_file_content,
    secure_error_response,
    log_security_event,
    SecurityConfig
)

invoices_api = Blueprint('invoices_api', __name__)

def extract_invoice_numbers_and_split(input_pdf: str, output_folder: str) -> bool:
    """Extract invoice numbers and split PDF"""
    if not PDF_AVAILABLE:
        raise ImportError("PDF processing library not available")
    
    reader = PdfReader(input_pdf)
    pattern = r'\b[P|R]\d{6,8}\b'  # Match invoice patterns
    invoices_found = False
    
    try:
        pages_by_invoice = {}
        
        # Extract text from each page and find invoice numbers
        for page_num, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                invoice_numbers = re.findall(pattern, text)
                if invoice_numbers:
                    invoices_found = True
                for invoice_number in invoice_numbers:
                    if invoice_number not in pages_by_invoice:
                        pages_by_invoice[invoice_number] = []
                    pages_by_invoice[invoice_number].append(page_num)
            except Exception as e:
                continue
        
        if not invoices_found:
            return False
        
        # Create separate PDFs for each invoice
        os.makedirs(output_folder, exist_ok=True)
        
        for invoice_number, page_nums in pages_by_invoice.items():
            writer = PdfWriter()
            for page_num in page_nums:
                if page_num < len(reader.pages):
                    writer.add_page(reader.pages[page_num])
            
            output_filename = os.path.join(output_folder, f"{invoice_number}.pdf")
            with open(output_filename, 'wb') as output_file:
                writer.write(output_file)
        
        return True
        
    except Exception as e:
        raise ValueError(f"PDF processing failed: {e}")

@invoices_api.route('/separate', methods=['POST'])
def separate_invoices():
    """Separate invoices from PDF file"""
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'pdf_file is required'}), 400
        
        pdf_file = request.files['pdf_file']
        
        if not pdf_file.filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        # Validate PDF file
        if not validate_filename(pdf_file.filename):
            return jsonify({'error': 'Invalid filename'}), 422
        
        pdf_validation = validate_file_content(pdf_file, SecurityConfig.ALLOWED_EXTENSIONS['pdf'])
        if not pdf_validation['valid']:
            return jsonify({'error': pdf_validation['error']}), 422
        
        # Save file
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = secure_filename(pdf_file.filename)
        file_path = os.path.join(upload_dir, filename)
        pdf_file.save(file_path)
        os.chmod(file_path, 0o600)
        
        # Create result folder
        separate_results_dir = 'separate_results'
        os.makedirs(separate_results_dir, exist_ok=True)
        
        result_folder = os.path.join(separate_results_dir, filename.rsplit('.', 1)[0], 'separateInvoices')
        
        # Process invoices
        invoices_found = extract_invoice_numbers_and_split(file_path, result_folder)
        
        if not invoices_found:
            return jsonify({'error': 'No invoices found in PDF'}), 400
        
        # Create ZIP file
        zip_filename = f"{filename.rsplit('.', 1)[0]}.zip"
        zip_path = os.path.join(separate_results_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(result_folder):
                for file in files:
                    file_path_in_zip = os.path.join(root, file)
                    arcname = os.path.relpath(file_path_in_zip, result_folder)
                    zipf.write(file_path_in_zip, arcname)
        
        # Count separated invoices
        invoice_count = len([f for f in os.listdir(result_folder) if f.endswith('.pdf')])
        
        return jsonify({
            'success': True,
            'message': f'Successfully separated {invoice_count} invoices',
            'invoice_count': invoice_count,
            'zip_filename': zip_filename,
            'download_url': f'/api/v1/invoices/download/{zip_filename}'
        })
        
    except Exception as e:
        # Cleanup on error
        file_path = locals().get('file_path')
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        log_security_event('invoice_separation_error', {'error': str(e)})
        return jsonify({'error': 'Invoice separation failed'}), 500

@invoices_api.route('/download/<filename>')
def download_invoices(filename):
    """Download separated invoices ZIP file"""
    try:
        if not validate_filename(filename):
            return jsonify({'error': 'Invalid filename'}), 422
        
        separate_results_dir = 'separate_results'
        secure_name = secure_filename(filename)
        zip_path = os.path.join(separate_results_dir, secure_name)
        
        # Prevent directory traversal
        if not os.path.abspath(zip_path).startswith(os.path.abspath(separate_results_dir)):
            return jsonify({'error': 'Access denied'}), 403
        
        if os.path.exists(zip_path):
            return send_file(zip_path, as_attachment=True, download_name=secure_name)
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'error': 'Download failed'}), 500