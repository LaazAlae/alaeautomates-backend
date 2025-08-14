###############################################################################
# ALAEAUTOMATES 2.0 BACKEND API
# Standalone Flask API for financial document processing
# Railway-ready deployment configuration
###############################################################################

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
from datetime import datetime, timedelta
import secrets

# Import API modules
from app.api.monthly_statements import monthly_statements_api
from app.api.invoices import invoices_api  
from app.api.excel_macros import excel_macros_api
from app.api.cc_batch import cc_batch_api
from app.utils.security import setup_security
from app.utils.cleanup_manager import cleanup_manager

###############################################################################
# APPLICATION CONFIGURATION
###############################################################################

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', secrets.token_hex(32)),
        'MAX_CONTENT_LENGTH': 50 * 1024 * 1024,  # 50MB
        'UPLOAD_FOLDER': os.path.join(os.getcwd(), 'uploads'),
        'RESULT_FOLDER': os.path.join(os.getcwd(), 'results'),
        'SEPARATE_RESULT_FOLDER': os.path.join(os.getcwd(), 'separate_results'),
    })
    
    # Create required directories
    for folder in ['uploads', 'results', 'separate_results']:
        os.makedirs(folder, exist_ok=True)
    
    # CORS configuration for frontend integration
    CORS(app, origins=["*"])  # Configure specific origins in production
    
    # Rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["1000 per day", "100 per hour", "20 per minute"],
        storage_uri="memory://"
    )
    limiter.init_app(app)
    
    # Setup security
    setup_security(app)
    
    # Register API blueprints
    app.register_blueprint(monthly_statements_api, url_prefix='/api/v1/monthly-statements')
    app.register_blueprint(invoices_api, url_prefix='/api/v1/invoices')
    app.register_blueprint(excel_macros_api, url_prefix='/api/v1/excel-macros')
    app.register_blueprint(cc_batch_api, url_prefix='/api/v1/cc-batch')
    
    # Exempt API from rate limiting (we'll handle it per endpoint)
    for blueprint_name in ['monthly_statements_api', 'invoices_api', 'excel_macros_api', 'cc_batch_api']:
        if blueprint_name in app.blueprints:
            limiter.exempt(app.blueprints[blueprint_name])
    
    ###############################################################################
    # MAIN API ROUTES
    ###############################################################################
    
    @app.route('/')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'AlaeAutomates 2.0 Backend API',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat(),
            'endpoints': [
                '/api/v1/help',
                '/api/v1/docs',
                '/visualizer - Interactive API Explorer',
                '/api/v1/cc-batch/docs - Credit Card Automation Documentation',
                '/api/v1/monthly-statements/*',
                '/api/v1/invoices/*',
                '/api/v1/excel-macros/*',
                '/api/v1/cc-batch/*'
            ]
        })
    
    @app.route('/api/v1/help')
    def api_help():
        return jsonify({
            'application': 'AlaeAutomates 2.0 Backend API',
            'description': 'Standalone REST API for financial document processing',
            'version': '2.0.0',
            'features': [
                {
                    'name': 'Monthly Statements Processing',
                    'description': 'Process PDF statements and Excel files to categorize transactions',
                    'endpoint': '/api/v1/monthly-statements/process'
                },
                {
                    'name': 'Invoice Separation',
                    'description': 'Split multi-invoice PDFs into separate files',
                    'endpoint': '/api/v1/invoices/separate'
                },
                {
                    'name': 'Excel Macros',
                    'description': 'Get VBA macro codes for Excel automation',
                    'endpoint': '/api/v1/excel-macros/cleanup'
                },
                {
                    'name': 'Credit Card Batch Processing',
                    'description': 'Process Excel files or text input and generate robust JavaScript automation code with legacy Edge compatibility',
                    'endpoint': '/api/v1/cc-batch/process'
                }
            ],
            'documentation_url': '/api/v1/docs',
            'deployment': 'Railway-ready'
        })
    
    @app.route('/api/v1/cc-batch/docs')
    def cc_batch_docs():
        return jsonify({
            'title': 'Credit Card Batch Processing API Documentation',
            'version': '2.0.0',
            'description': 'Robust credit card automation with legacy Edge compatibility',
            'base_url': '/api/v1/cc-batch',
            'features': {
                'legacy_browser_support': 'Works with Legacy Edge and Internet Explorer',
                'input_validation': 'Checks field visibility before attempting to fill',
                'execution_safeguards': 'Prevents record skipping with timing controls',
                'robust_automation': 'Enhanced error handling and recovery',
                'dual_input_modes': 'Supports both Excel file upload and text input'
            },
            'endpoints': {
                'POST /process': {
                    'description': 'Process Excel file for credit card automation',
                    'input': 'multipart/form-data with excel_file',
                    'output': 'Robust JavaScript automation code',
                    'example': {
                        'curl': 'curl -X POST -F "excel_file=@data.xlsx" /api/v1/cc-batch/process'
                    }
                },
                'POST /parse-excel-text': {
                    'description': 'Parse Excel data from text input (frontend compatible)',
                    'input': 'JSON with excel_text field',
                    'output': 'Same robust JavaScript automation code',
                    'example': {
                        'data': {
                            'excel_text': 'R130587    AMEX-1006    105.00    Wanyi Yang\\nR131702    AMEX-1007    210.00    Virginia Clarke'
                        }
                    }
                },
                'POST /download-code': {
                    'description': 'Download generated JavaScript as file',
                    'input': 'JSON with code field',
                    'output': 'JavaScript file download'
                }
            },
            'usage_instructions': {
                'step_1': 'Generate automation code using /process or /parse-excel-text',
                'step_2': 'Copy the generated JavaScript code',
                'step_3': 'Navigate to your payment processing page',
                'step_4': 'Open browser console (F12)',
                'step_5': 'Paste code and press Enter',
                'step_6': 'Click the green triangle on each page to continue automation'
            },
            'generated_code_features': {
                'execution_lock': 'Prevents double-clicking issues',
                'visibility_checks': 'Validates fields are visible before filling',
                'legacy_events': 'Uses fireEvent for older browsers',
                'robust_timing': '800-2000ms delays between operations',
                'error_recovery': 'Graceful failure handling',
                'progress_tracking': 'Cookie-based progress persistence'
            },
            'browser_compatibility': {
                'legacy_edge': 'Full support with fireEvent fallbacks',
                'internet_explorer': 'Compatible event handling',
                'modern_browsers': 'Full feature support',
                'tested_versions': ['Edge Legacy', 'IE 11+', 'Chrome 60+', 'Firefox 55+']
            }
        })

    @app.route('/visualizer')
    def api_visualizer():
        """Serve the API visualizer interface"""
        from flask import send_from_directory
        return send_from_directory('Visualiser', 'index.html')
    
    @app.route('/visualizer/<path:filename>')
    def visualizer_assets(filename):
        """Serve visualizer static assets with proper MIME types"""
        from flask import send_from_directory, Response
        import mimetypes
        
        # Set proper MIME types
        if filename.endswith('.css'):
            mimetype = 'text/css'
        elif filename.endswith('.js'):
            mimetype = 'application/javascript'
        else:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        response = send_from_directory('Visualiser', filename)
        response.headers['Content-Type'] = mimetype
        return response

    @app.route('/api/v1/docs')
    def api_docs():
        return jsonify({
            'title': 'AlaeAutomates 2.0 Backend API Documentation',
            'version': '2.0.0',
            'description': 'Complete REST API for financial document automation',
            'base_url': '/api/v1',
            'authentication': 'None required',
            'cors': 'Enabled for all origins',
            'rate_limits': {
                'daily': 1000,
                'hourly': 100,
                'per_minute': 20
            },
            'file_limits': {
                'max_size': '50MB',
                'allowed_types': ['PDF', 'Excel (.xlsx, .xls)']
            },
            'credit_card_automation_features': {
                'legacy_edge_compatible': True,
                'visibility_checks': 'Input fields validated before filling',
                'record_skipping_prevention': 'Execution locks and timing safeguards',
                'robust_timing_controls': 'Enhanced delays and failsafe mechanisms',
                'usage_method': 'Click green triangle to execute each step',
                'supported_browsers': ['Legacy Edge', 'Internet Explorer', 'Modern browsers']
            },
            'endpoints': {
                'monthly_statements': {
                    'POST /monthly-statements/process': 'Start processing PDF and Excel files',
                    'GET /monthly-statements/status/{session_id}': 'Check processing status',
                    'GET /monthly-statements/questions/{session_id}': 'Get current question',
                    'POST /monthly-statements/questions/{session_id}/answer': 'Answer question',
                    'GET /monthly-statements/results/{session_id}': 'Get processing results',
                    'GET /monthly-statements/download/{session_id}': 'Download results ZIP'
                },
                'invoices': {
                    'POST /invoices/separate': 'Separate invoices from PDF',
                    'GET /invoices/download/{filename}': 'Download separated invoices'
                },
                'excel_macros': {
                    'GET /excel-macros/cleanup': 'Get cleanup macro code',
                    'GET /excel-macros/sort': 'Get sort & sum macro code'
                },
                'cc_batch': {
                    'POST /cc-batch/process': 'Process Excel file for robust CC automation (legacy Edge compatible)',
                    'POST /cc-batch/parse-excel-text': 'Parse Excel data from text input (frontend compatible, robust output)',
                    'POST /cc-batch/download-code': 'Download generated JavaScript automation code',
                    'GET /cc-batch/docs': 'Detailed credit card automation documentation'
                }
            },
            'deployment': {
                'platform': 'Railway',
                'cost': 'Free tier available',
                'auto_deploy': 'Connected to GitHub'
            }
        })
    
    ###############################################################################
    # ERROR HANDLERS
    ###############################################################################
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found', 'available_endpoints': '/api/v1/help'}), 404
    
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server error: {error}')
        return jsonify({'error': 'Internal server error'}), 500
    
    ###############################################################################
    # LOGGING SETUP
    ###############################################################################
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    return app

###############################################################################
# APPLICATION STARTUP
###############################################################################

app = create_app()

if __name__ == '__main__':
    # Start cleanup manager
    cleanup_manager.start_background_cleanup()
    
    # Get port from environment (Railway sets PORT automatically)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=False)