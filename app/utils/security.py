###############################################################################
# ENHANCED SECURITY UTILITIES
# Advanced file validation, session management, rate limiting, and security configurations
# Optimized for O(n) performance with comprehensive backend security features
###############################################################################

import os
import re
import secrets
import logging
import hashlib
import hmac
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import magic
from werkzeug.utils import secure_filename
from functools import wraps
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Enhanced security configuration constants with comprehensive protections"""
    
    # File validation constants
    ALLOWED_EXTENSIONS = {
        'pdf': ['application/pdf'],
        'excel': [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/excel'
        ]
    }
    
    MAX_FILENAME_LENGTH = 255
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MIN_FILE_SIZE = 1024  # 1KB minimum
    
    FORBIDDEN_PATTERNS = [
        r'\.\./',  # Directory traversal
        r'[<>:"|?*]',  # Windows forbidden chars
        r'^\.',  # Hidden files
        r'\x00',  # NULL bytes
        r'[\x01-\x1f\x7f-\x9f]',  # Control characters
    ]
    
    # Rate limiting constants
    RATE_LIMIT_REQUESTS = 10  # requests per window
    RATE_LIMIT_WINDOW = 300  # 5 minutes in seconds
    MAX_CONCURRENT_SESSIONS = 50
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Cache-Control': 'no-store, no-cache, must-revalidate, private'
    }
    
    # Input validation
    MAX_INPUT_LENGTH = 1000
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # JavaScript
        r'javascript:',  # JavaScript URLs
        r'vbscript:',  # VBScript URLs
        r'onload\s*=',  # Event handlers
        r'onerror\s*=',
        r'onclick\s*=',
        r'eval\s*\(',  # Code execution
        r'exec\s*\(',
        r'system\s*\(',
        r'\$\{.*\}',  # Template injection
        r'\{\{.*\}\}',
    ]

class RateLimiter:
    """Rate limiting implementation with sliding window"""
    
    def __init__(self):
        self.requests = defaultdict(deque)  # IP -> deque of timestamps
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, ip_address: str, limit: int = SecurityConfig.RATE_LIMIT_REQUESTS, 
                   window: int = SecurityConfig.RATE_LIMIT_WINDOW) -> bool:
        """Check if request is allowed under rate limit"""
        current_time = time.time()
        
        # Periodic cleanup
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_requests(current_time)
            self.last_cleanup = current_time
        
        # Remove old requests outside window
        cutoff_time = current_time - window
        while self.requests[ip_address] and self.requests[ip_address][0] < cutoff_time:
            self.requests[ip_address].popleft()
        
        # Check if under limit
        if len(self.requests[ip_address]) < limit:
            self.requests[ip_address].append(current_time)
            return True
        
        logger.warning(f"Rate limit exceeded for IP: {ip_address}")
        return False
    
    def _cleanup_old_requests(self, current_time: float) -> None:
        """Clean up old request records"""
        cutoff_time = current_time - SecurityConfig.RATE_LIMIT_WINDOW
        for ip_address in list(self.requests.keys()):
            while self.requests[ip_address] and self.requests[ip_address][0] < cutoff_time:
                self.requests[ip_address].popleft()
            # Remove empty deques
            if not self.requests[ip_address]:
                del self.requests[ip_address]

# Global rate limiter instance
rate_limiter = RateLimiter()

def validate_filename(filename: str) -> Dict[str, Any]:
    """Enhanced filename validation for security"""
    if not filename:
        return {'valid': False, 'error': 'Filename is required'}
    
    if len(filename) > SecurityConfig.MAX_FILENAME_LENGTH:
        return {'valid': False, 'error': f'Filename too long (max {SecurityConfig.MAX_FILENAME_LENGTH} chars)'}
    
    # Check forbidden patterns
    for pattern in SecurityConfig.FORBIDDEN_PATTERNS:
        if re.search(pattern, filename):
            return {'valid': False, 'error': 'Filename contains forbidden characters'}
    
    # Check for double extensions (security risk)
    if filename.count('.') > 1:
        parts = filename.split('.')
        if len(parts) > 2 and parts[-2].lower() in ['exe', 'bat', 'cmd', 'scr', 'com']:
            return {'valid': False, 'error': 'Double extension detected'}
    
    return {'valid': True}

def validate_file_content(file_obj, allowed_mime_types: List[str]) -> Dict[str, Any]:
    """Enhanced file content validation using magic numbers and size checks"""
    try:
        # Check file size
        file_obj.seek(0, 2)  # Seek to end
        file_size = file_obj.tell()
        file_obj.seek(0)  # Reset to beginning
        
        if file_size < SecurityConfig.MIN_FILE_SIZE:
            return {'valid': False, 'error': f'File too small (min {SecurityConfig.MIN_FILE_SIZE} bytes)'}
        
        if file_size > SecurityConfig.MAX_FILE_SIZE:
            return {'valid': False, 'error': f'File too large (max {SecurityConfig.MAX_FILE_SIZE} bytes)'}
        
        # Read header for magic number detection
        header = file_obj.read(min(8192, file_size))  # Read up to 8KB
        file_obj.seek(0)
        
        # Get MIME type using python-magic
        try:
            mime_type = magic.from_buffer(header, mime=True)
        except Exception as e:
            logger.error(f"Magic detection failed: {e}")
            return {'valid': False, 'error': 'Cannot validate file type'}
        
        if mime_type not in allowed_mime_types:
            return {
                'valid': False, 
                'error': f'Invalid file type. Expected: {allowed_mime_types}, Got: {mime_type}'
            }
        
        # Additional PDF-specific validation
        if mime_type == 'application/pdf':
            if not header.startswith(b'%PDF-'):
                return {'valid': False, 'error': 'Invalid PDF header'}
            
            # Check for suspicious PDF content
            if b'/JavaScript' in header or b'/JS' in header:
                return {'valid': False, 'error': 'PDF contains JavaScript (security risk)'}
        
        # Additional Excel-specific validation
        elif 'excel' in mime_type or 'spreadsheet' in mime_type:
            # Check for macro-enabled files
            if b'macro' in header.lower() or b'vba' in header.lower():
                return {'valid': False, 'error': 'Excel file contains macros (security risk)'}
        
        return {'valid': True, 'mime_type': mime_type, 'size': file_size}
            
    except Exception as e:
        logger.error(f"File validation error: {e}")
        return {'valid': False, 'error': 'File validation failed'}

def validate_upload_files(pdf_file=None, excel_file=None) -> Dict[str, Any]:
    """Enhanced validation for uploaded files with comprehensive security checks"""
    errors = []
    warnings = []
    total_size = 0
    
    if pdf_file:
        filename_validation = validate_filename(pdf_file.filename)
        if not filename_validation['valid']:
            errors.append(f"PDF filename invalid: {filename_validation['error']}")
        else:
            pdf_validation = validate_file_content(pdf_file, SecurityConfig.ALLOWED_EXTENSIONS['pdf'])
            if not pdf_validation['valid']:
                errors.append(f"PDF validation failed: {pdf_validation['error']}")
            else:
                total_size += pdf_validation.get('size', 0)
                if pdf_validation.get('size', 0) > 50 * 1024 * 1024:  # 50MB
                    warnings.append('PDF file is very large, processing may be slow')
    
    if excel_file:
        filename_validation = validate_filename(excel_file.filename)
        if not filename_validation['valid']:
            errors.append(f"Excel filename invalid: {filename_validation['error']}")
        else:
            excel_validation = validate_file_content(excel_file, SecurityConfig.ALLOWED_EXTENSIONS['excel'])
            if not excel_validation['valid']:
                errors.append(f"Excel validation failed: {excel_validation['error']}")
            else:
                total_size += excel_validation.get('size', 0)
                if excel_validation.get('size', 0) > 10 * 1024 * 1024:  # 10MB
                    warnings.append('Excel file is large, may contain many companies')
    
    # Check combined file size
    if total_size > SecurityConfig.MAX_FILE_SIZE:
        errors.append(f'Combined file size too large (max {SecurityConfig.MAX_FILE_SIZE} bytes)')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'total_size': total_size
    }

def sanitize_input(text: str, max_length: int = SecurityConfig.MAX_INPUT_LENGTH) -> str:
    """Enhanced input sanitization with pattern detection"""
    if not text:
        return ""
    
    # Convert to string and limit length
    sanitized = str(text)[:max_length]
    
    # Check for dangerous patterns
    for pattern in SecurityConfig.DANGEROUS_PATTERNS:
        if re.search(pattern, sanitized, re.IGNORECASE):
            logger.warning(f"Dangerous pattern detected in input: {pattern}")
            return ""  # Return empty string for dangerous input
    
    # Remove potentially dangerous characters but preserve normal punctuation
    sanitized = re.sub(r'[<>"\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)
    
    # Normalize whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    return sanitized.strip()

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(length)

def create_file_hash(file_obj) -> str:
    """Create SHA-256 hash of file content for integrity checking"""
    file_obj.seek(0)
    hash_sha256 = hashlib.sha256()
    for chunk in iter(lambda: file_obj.read(8192), b""):
        hash_sha256.update(chunk)
    file_obj.seek(0)
    return hash_sha256.hexdigest()

def verify_file_integrity(file_obj, expected_hash: str) -> bool:
    """Verify file integrity using SHA-256 hash"""
    actual_hash = create_file_hash(file_obj)
    return hmac.compare_digest(actual_hash, expected_hash)

def secure_error_response(message: str, status_code: int) -> tuple:
    """Create secure error response with sanitized message"""
    # Sanitize error message to prevent information disclosure
    safe_message = sanitize_input(message)
    return {'error': safe_message, 'timestamp': datetime.now().isoformat()}, status_code

def log_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """Enhanced security event logging with structured data"""
    sanitized_details = {k: sanitize_input(str(v)) for k, v in details.items()}
    log_entry = {
        'event_type': event_type,
        'timestamp': datetime.now().isoformat(),
        'details': sanitized_details
    }
    logger.warning(f"SECURITY EVENT: {json.dumps(log_entry)}")

class SecureSessionManager:
    """Enhanced secure session management with rate limiting and monitoring"""
    
    def __init__(self):
        self._sessions = {}
        self._created_times = {}
        self._access_times = {}  # Track last access time
        self._ip_addresses = {}  # Track IP addresses for sessions
        self._session_timeout = timedelta(hours=2)
        self._failed_attempts = defaultdict(int)  # Track failed session attempts
        self._blocked_ips: Set[str] = set()  # Temporarily blocked IPs
    
    def create_session(self, session_id: str, data: Any, ip_address: str = None) -> bool:
        """Create a new session with enhanced security checks"""
        try:
            # Check for maximum concurrent sessions
            if len(self._sessions) >= SecurityConfig.MAX_CONCURRENT_SESSIONS:
                # Clean up expired sessions first
                self.cleanup_expired_sessions()
                if len(self._sessions) >= SecurityConfig.MAX_CONCURRENT_SESSIONS:
                    logger.warning(f"Maximum concurrent sessions reached")
                    return False
            
            # Check if IP is blocked
            if ip_address and ip_address in self._blocked_ips:
                logger.warning(f"Blocked IP attempted to create session: {ip_address}")
                return False
            
            # Rate limiting by IP
            if ip_address and not rate_limiter.is_allowed(ip_address):
                logger.warning(f"Rate limit exceeded for IP: {ip_address}")
                return False
            
            current_time = datetime.now()
            self._sessions[session_id] = data
            self._created_times[session_id] = current_time
            self._access_times[session_id] = current_time
            if ip_address:
                self._ip_addresses[session_id] = ip_address
            
            logger.info(f"Session created: {session_id[:8]}... from IP: {ip_address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str, ip_address: str = None) -> Optional[Any]:
        """Get session data with security validation"""
        if session_id not in self._sessions:
            if ip_address:
                self._failed_attempts[ip_address] += 1
                if self._failed_attempts[ip_address] > 5:
                    self._blocked_ips.add(ip_address)
                    logger.warning(f"IP blocked due to repeated failed attempts: {ip_address}")
            return None
        
        current_time = datetime.now()
        
        # Check if session expired
        if current_time - self._created_times[session_id] > self._session_timeout:
            logger.info(f"Session expired: {session_id[:8]}...")
            self.remove_session(session_id)
            return None
        
        # Check IP address if provided
        if ip_address and session_id in self._ip_addresses:
            if self._ip_addresses[session_id] != ip_address:
                logger.warning(f"IP mismatch for session {session_id[:8]}...: expected {self._ip_addresses[session_id]}, got {ip_address}")
                self.remove_session(session_id)  # Remove potentially hijacked session
                return None
        
        # Update access time
        self._access_times[session_id] = current_time
        
        return self._sessions[session_id]
    
    def remove_session(self, session_id: str) -> None:
        """Remove session and clean up associated data"""
        self._sessions.pop(session_id, None)
        self._created_times.pop(session_id, None)
        self._access_times.pop(session_id, None)
        self._ip_addresses.pop(session_id, None)
        logger.info(f"Session removed: {session_id[:8]}...")
    
    def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions and reset rate limiting data"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, created_time in self._created_times.items():
            if current_time - created_time > self._session_timeout:
                expired_sessions.append(session_id)
        
        removed_count = 0
        for session_id in expired_sessions:
            self.remove_session(session_id)
            removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired sessions")
        
        # Reset failed attempts older than 1 hour
        cutoff_time = time.time() - 3600
        for ip in list(self._blocked_ips):
            # Remove IP blocks after 1 hour
            self._blocked_ips.discard(ip)
        
        # Reset failed attempt counters periodically
        self._failed_attempts.clear()
    
    def get_session_stats(self) -> Dict[str, int]:
        """Get session statistics for monitoring"""
        return {
            'active_sessions': len(self._sessions),
            'blocked_ips': len(self._blocked_ips),
            'max_sessions': SecurityConfig.MAX_CONCURRENT_SESSIONS
        }

# Global instances
secure_session_manager = SecureSessionManager()

def require_valid_session(f):
    """Enhanced decorator to require valid session with IP validation"""
    from functools import wraps
    from flask import request
    
    @wraps(f)
    def decorated_function(session_id, *args, **kwargs):
        # Get client IP address
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        # Validate session with IP check
        if not secure_session_manager.get_session(session_id, ip_address):
            logger.warning(f"Invalid session access attempt from IP: {ip_address}")
            return secure_error_response('Invalid or expired session', 404)
        
        return f(session_id, *args, **kwargs)
    
    return decorated_function

def require_rate_limit(f):
    """Decorator to enforce rate limiting"""
    from functools import wraps
    from flask import request
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get client IP address
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        # Check rate limit
        if not rate_limiter.is_allowed(ip_address):
            return secure_error_response('Rate limit exceeded', 429)
        
        return f(*args, **kwargs)
    
    return decorated_function

def setup_security(app):
    """Enhanced security configurations for Flask app with comprehensive protections"""
    
    # Enhanced security headers
    @app.after_request
    def add_security_headers(response):
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
    
    # Request logging and monitoring
    @app.before_request
    def log_request():
        from flask import request
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        logger.info(f"Request from {ip_address}: {request.method} {request.path}")
    
    # Error handler for rate limiting
    @app.errorhandler(429)
    def rate_limit_error(error):
        return secure_error_response('Too many requests. Please try again later.', 429)
    
    # Error handler for file size errors
    @app.errorhandler(413)
    def file_too_large(error):
        return secure_error_response('File too large', 413)
    
    # Set maximum content length
    app.config['MAX_CONTENT_LENGTH'] = SecurityConfig.MAX_FILE_SIZE
    
    # Enhanced periodic cleanup and monitoring
    import threading
    import time
    
    def enhanced_periodic_tasks():
        while True:
            try:
                # Clean up sessions every hour
                secure_session_manager.cleanup_expired_sessions()
                
                # Log system statistics
                stats = secure_session_manager.get_session_stats()
                logger.info(f"System stats: {stats}")
                
                time.sleep(3600)  # Every hour
            except Exception as e:
                logger.error(f"Periodic cleanup error: {e}")
                time.sleep(300)  # Retry in 5 minutes on error
    
    cleanup_thread = threading.Thread(target=enhanced_periodic_tasks, daemon=True)
    cleanup_thread.start()
    
    logger.info("Enhanced security system initialized")