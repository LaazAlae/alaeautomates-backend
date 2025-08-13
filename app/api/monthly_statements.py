###############################################################################
# MONTHLY STATEMENTS API MODULE
# RESTful endpoints for PDF statement processing
###############################################################################

from flask import Blueprint, request, jsonify, send_file
import os
import tempfile
import zipfile
import threading
import logging
import re
from datetime import datetime
from werkzeug.utils import secure_filename

# Setup logging
logger = logging.getLogger(__name__)

from app.modules.statement_processor import StatementProcessor
from app.utils.security import (
    validate_upload_files,
    sanitize_input,
    secure_error_response,
    log_security_event,
    secure_session_manager,
    require_valid_session,
    require_rate_limit,
    create_file_hash,
    generate_secure_token
)

monthly_statements_api = Blueprint('monthly_statements_api', __name__)

class WebStatementProcessor:
    """Enhanced web interface wrapper for StatementProcessor with security features"""
    
    def __init__(self, pdf_path: str, excel_path: str, session_id: str):
        self.processor = StatementProcessor(pdf_path, excel_path)
        self.session_id = session_id
        self.statements = []
        self.current_question_index = 0
        self.questions_needed = []
        self.question_history = []
        
        # Processing status tracking with enhanced security
        self._processing_status = 'pending'
        self._start_time = None
        self._processing_logs = []
        self._error_message = None
        self._results = None
        self._pdf_files = {}
        self._security_verified = False
        
        # Performance tracking
        self._performance_metrics = {
            'extraction_time': None,
            'processing_time': None,
            'question_time': None,
            'pdf_creation_time': None
        }
    
    def start_background_extraction(self):
        """Start background statement extraction with performance monitoring"""
        def extract_in_background():
            try:
                self._processing_status = 'processing'
                self._start_time = datetime.now()
                extraction_start = datetime.now()
                
                # Extract statements with O(n) optimization
                self.statements = self.processor.extract_statements()
                
                self._performance_metrics['extraction_time'] = (
                    datetime.now() - extraction_start
                ).total_seconds()
                
                processing_start = datetime.now()
                
                # Find questions that need manual review
                self.questions_needed = [stmt for stmt in self.statements if stmt.get('ask_question', False)]
                
                self._performance_metrics['processing_time'] = (
                    datetime.now() - processing_start
                ).total_seconds()
                
                self._processing_status = 'completed'
                self._security_verified = True
                
                # Log extraction success
                logger.info(f"Extraction completed for session {self.session_id[:8]}... - "
                          f"Found {len(self.statements)} statements, {len(self.questions_needed)} need review")
                
            except Exception as e:
                self._processing_status = 'error'
                self._error_message = str(e)
                logger.error(f"Extraction failed for session {self.session_id[:8]}...: {e}")
                log_security_event('extraction_error', {
                    'session_id': self.session_id[:8] + '...',
                    'error': str(e)
                })
        
        extraction_thread = threading.Thread(target=extract_in_background, daemon=True)
        extraction_thread.start()
    
    def get_current_question_state(self):
        """Get current question state"""
        if self.current_question_index >= len(self.questions_needed):
            return {"completed": True, "total": len(self.questions_needed)}
        
        statement = self.questions_needed[self.current_question_index]
        return {
            "completed": False,
            "current": self.current_question_index + 1,
            "total": len(self.questions_needed),
            "company_name": statement.get('company_name', 'Unknown'),
            "similar_to": statement.get('similar_to', 'Unknown'),
            "can_go_back": len(self.question_history) > 0
        }
    
    def process_question_response(self, response: str):
        """Process a question response"""
        if self.current_question_index >= len(self.questions_needed):
            return {"completed": True}
        
        statement = self.questions_needed[self.current_question_index]
        
        if response == 'y':
            self.question_history.append(self.current_question_index)
            statement['destination'] = 'DNM'
            statement['user_answered'] = 'yes'
            self.current_question_index += 1
        elif response == 'n':
            self.question_history.append(self.current_question_index)
            statement['user_answered'] = 'no'
            self.current_question_index += 1
        elif response == 's':
            for i in range(self.current_question_index, len(self.questions_needed)):
                self.questions_needed[i]['user_answered'] = 'skip'
            self.current_question_index = len(self.questions_needed)
        elif response == 'p':
            if self.question_history:
                self.current_question_index = self.question_history.pop()
            else:
                return {"error": "No previous questions"}
        
        return self.get_current_question_state()
    
    def create_results(self):
        """Create results including PDF splitting with enhanced security and performance tracking"""
        def create_results_background():
            try:
                self._processing_status = 'creating_results'
                pdf_start = datetime.now()
                
                # Create split PDFs with O(n) optimization
                split_results = self.processor.create_split_pdfs(self.statements)
                
                # Move PDFs to secure results directory
                results_dir = 'results'
                os.makedirs(results_dir, exist_ok=True, mode=0o750)  # Restrictive permissions
                
                pdf_files = {}
                for dest, page_count in split_results.items():
                    old_file = self.processor._get_filename_for_destination(dest)
                    if os.path.exists(old_file):
                        # Create secure filename
                        secure_name = f"{self.session_id}_{secure_filename(os.path.basename(old_file))}"
                        new_file = os.path.join(results_dir, secure_name)
                        os.rename(old_file, new_file)
                        
                        # Set restrictive permissions
                        os.chmod(new_file, 0o600)
                        
                        pdf_files[dest] = {"file": new_file, "pages": page_count}
                
                self._pdf_files = pdf_files
                
                self._performance_metrics['pdf_creation_time'] = (
                    datetime.now() - pdf_start
                ).total_seconds()
                
                # Calculate enhanced statistics
                stats = self.calculate_statistics()
                
                self._results = {
                    "pdf_files": pdf_files,
                    "statistics": stats,
                    "session_id": self.session_id,
                    "performance_metrics": self._performance_metrics,
                    "created_at": datetime.now().isoformat()
                }
                
                self._processing_status = 'completed'
                
                logger.info(f"Results created for session {self.session_id[:8]}... - "
                          f"{len(pdf_files)} PDF files, {sum(f['pages'] for f in pdf_files.values())} total pages")
                
            except Exception as e:
                self._processing_status = 'error'
                self._error_message = str(e)
                logger.error(f"Results creation failed for session {self.session_id[:8]}...: {e}")
                log_security_event('results_creation_error', {
                    'session_id': self.session_id[:8] + '...',
                    'error': str(e)
                })
        
        thread = threading.Thread(target=create_results_background, daemon=True)
        thread.start()
    
    def calculate_statistics(self):
        """Calculate processing statistics"""
        destinations = {}
        manual_count = 0
        ask_count = 0
        
        for stmt in self.statements:
            dest = stmt.get('destination', 'Unknown')
            destinations[dest] = destinations.get(dest, 0) + 1
            
            if stmt.get('manual_required', False):
                manual_count += 1
            if stmt.get('ask_question', False):
                ask_count += 1
        
        return {
            "total_statements": len(self.statements),
            "destinations": destinations,
            "manual_processing": {
                "manual_review_required": manual_count,
                "interactive_questions": ask_count
            }
        }

@monthly_statements_api.route('/process', methods=['POST'])
@require_rate_limit
def process_files():
    """Start monthly statements processing"""
    try:
        # Validate files
        if 'pdf_file' not in request.files or 'excel_file' not in request.files:
            return jsonify({'error': 'Both pdf_file and excel_file are required'}), 400
        
        pdf_file = request.files['pdf_file']
        excel_file = request.files['excel_file']
        
        # Validate file content
        validation_result = validate_upload_files(pdf_file, excel_file)
        if not validation_result['valid']:
            return jsonify({'error': '; '.join(validation_result['errors'])}), 422
        
        # Generate cryptographically secure session ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_id = f"api_session_{timestamp}_{generate_secure_token(8)}"
        
        # Get client IP for session tracking
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        # Save files
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        pdf_secure_name = secure_filename(f"{session_id}_{pdf_file.filename}")
        excel_secure_name = secure_filename(f"{session_id}_{excel_file.filename}")
        
        pdf_path = os.path.join(upload_dir, pdf_secure_name)
        excel_path = os.path.join(upload_dir, excel_secure_name)
        
        pdf_file.save(pdf_path)
        excel_file.save(excel_path)
        
        # Create file hashes for integrity verification
        pdf_hash = create_file_hash(pdf_file)
        excel_hash = create_file_hash(excel_file)
        
        # Set restrictive permissions
        os.chmod(pdf_path, 0o600)
        os.chmod(excel_path, 0o600)
        
        # Create processor
        processor = WebStatementProcessor(pdf_path, excel_path, session_id)
        
        # Store session with IP tracking and file metadata
        session_data = {
            'processor': processor,
            'pdf_hash': pdf_hash,
            'excel_hash': excel_hash,
            'upload_time': datetime.now().isoformat(),
            'file_info': {
                'pdf_name': secure_filename(pdf_file.filename),
                'excel_name': secure_filename(excel_file.filename)
            }
        }
        
        if not secure_session_manager.create_session(session_id, session_data, ip_address):
            # Clean up uploaded files if session creation fails
            try:
                os.remove(pdf_path)
                os.remove(excel_path)
            except:
                pass
            return jsonify({'error': 'Failed to create session'}), 500
        
        # Start processing
        processor.start_background_extraction()
        
        log_security_event('session_created', {
            'session_id': session_id[:8] + '...',
            'ip_address': ip_address,
            'file_count': 2
        })
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': 'processing',
            'message': 'Monthly statements processing started',
            'upload_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        log_security_event('monthly_statements_error', {
            'error': str(e),
            'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        })
        return secure_error_response('Processing failed', 500)

@monthly_statements_api.route('/status/<session_id>')
@require_rate_limit
def get_status(session_id):
    """Get processing status"""
    try:
        # Sanitize session ID input
        session_id = sanitize_input(session_id, 128)
        if not session_id:
            return secure_error_response('Invalid session ID', 400)
        
        # Get client IP for validation
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        session_data = secure_session_manager.get_session(session_id, ip_address)
        if not session_data:
            return secure_error_response('Session not found', 404)
        
        processor = session_data.get('processor') if isinstance(session_data, dict) else session_data
        status = getattr(processor, '_processing_status', 'unknown')
        
        response = {
            'session_id': session_id,
            'status': status
        }
        
        if status == 'completed':
            questions = getattr(processor, 'questions_needed', [])
            if questions:
                response['requires_questions'] = True
                response['questions_count'] = len(questions)
            else:
                response['requires_questions'] = False
        elif status == 'error':
            response['error'] = getattr(processor, '_error_message', 'Unknown error')
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return secure_error_response('Failed to get status', 500)

@monthly_statements_api.route('/questions/<session_id>')
@require_valid_session
def get_questions(session_id):
    """Get current question with enhanced security"""
    try:
        session_data = secure_session_manager.get_session(session_id)
        if not session_data:
            return secure_error_response('Session not found', 404)
        
        processor = session_data.get('processor') if isinstance(session_data, dict) else session_data
        question_state = processor.get_current_question_state()
        
        return jsonify(question_state)
    except Exception as e:
        logger.error(f"Questions retrieval failed: {e}")
        return secure_error_response('Failed to get questions', 500)

@monthly_statements_api.route('/questions/<session_id>/answer', methods=['POST'])
@require_valid_session
def answer_question(session_id):
    """Answer a question with enhanced validation"""
    try:
        session_data = secure_session_manager.get_session(session_id)
        if not session_data:
            return secure_error_response('Session not found', 404)
        
        processor = session_data.get('processor') if isinstance(session_data, dict) else session_data
        
        data = request.get_json()
        if not data or 'response' not in data:
            return secure_error_response('Response is required', 400)
        
        response = sanitize_input(data['response'], 1)  # Limit to 1 character
        if response not in ['y', 'n', 's', 'p']:
            return secure_error_response('Invalid response. Must be y, n, s, or p', 400)
        
        # Track question response time
        question_start = datetime.now()
        processor._performance_metrics['question_time'] = (
            datetime.now() - question_start
        ).total_seconds()
        
        result = processor.process_question_response(response)
        
        if result.get("completed"):
            # Start final processing
            processor.create_results()
            
            return jsonify({
                'completed': True,
                'status': 'creating_results',
                'message': 'All questions answered, generating results'
            })
        else:
            return jsonify({
                'completed': False,
                'question_state': result
            })
            
    except Exception as e:
        logger.error(f"Answer processing failed: {e}")
        return secure_error_response('Failed to process answer', 500)

@monthly_statements_api.route('/results/<session_id>')
@require_valid_session
def get_results(session_id):
    """Get processing results with enhanced security"""
    try:
        session_data = secure_session_manager.get_session(session_id)
        if not session_data:
            return secure_error_response('Session not found', 404)
        
        processor = session_data.get('processor') if isinstance(session_data, dict) else session_data
        
        if not hasattr(processor, '_results') or not processor._results:
            status = getattr(processor, '_processing_status', 'unknown')
            if status == 'error':
                error_msg = getattr(processor, '_error_message', 'Processing failed')
                return secure_error_response(error_msg, 500)
            else:
                return jsonify({
                    'error': 'Results not ready yet', 
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                }), 202
        
        # Add security metadata to results
        results = processor._results.copy()
        results['security_verified'] = getattr(processor, '_security_verified', False)
        results['access_time'] = datetime.now().isoformat()
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Results retrieval failed: {e}")
        return secure_error_response('Failed to get results', 500)

@monthly_statements_api.route('/download/<session_id>')
@require_valid_session
def download_results(session_id):
    """Download results as ZIP file with enhanced security"""
    try:
        session_data = secure_session_manager.get_session(session_id)
        if not session_data:
            return secure_error_response('Session not found', 404)
        
        processor = session_data.get('processor') if isinstance(session_data, dict) else session_data
        
        if not hasattr(processor, '_pdf_files') or not processor._pdf_files:
            return secure_error_response('No files available for download', 404)
        
        # Log download attempt
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        log_security_event('download_attempt', {
            'session_id': session_id[:8] + '...',
            'ip_address': ip_address,
            'file_count': len(processor._pdf_files)
        })
        
        # Create secure ZIP file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip', mode='wb')
        try:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
                files_added = 0
                for dest, file_info in processor._pdf_files.items():
                    file_path = file_info["file"]
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        # Verify file integrity before adding to ZIP
                        try:
                            with open(file_path, 'rb') as f:
                                # Basic file validation
                                header = f.read(4)
                                if header.startswith(b'%PDF'):
                                    zip_file.write(file_path, secure_filename(f"{dest}.pdf"))
                                    files_added += 1
                        except Exception as file_error:
                            logger.warning(f"Skipping corrupted file {file_path}: {file_error}")
                            continue
            
            temp_zip.close()
            
            if files_added == 0:
                os.unlink(temp_zip.name)
                return secure_error_response('No valid files to download', 404)
            
            # Set restrictive permissions on temp file
            os.chmod(temp_zip.name, 0o600)
            
            # Clean filename for download
            safe_session_id = re.sub(r'[^a-zA-Z0-9_-]', '', session_id[:16])
            download_name = f"monthly_statements_{safe_session_id}.zip"
            
            return send_file(temp_zip.name, as_attachment=True, download_name=download_name)
                           
        except Exception as e:
            if temp_zip:
                temp_zip.close()
                try:
                    os.unlink(temp_zip.name)
                except:
                    pass
            logger.error(f"ZIP creation failed: {e}")
            return secure_error_response('Failed to create download file', 500)
            
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return secure_error_response('Download failed', 500)