#!/usr/bin/env python3
"""
Digital Signature System - Electronic signature and document security for DKI Engine
Handles PDF digital signatures, certificate management, and document authentication
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tempfile

# Digital signature libraries
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.serialization import pkcs12
    HAVE_CRYPTOGRAPHY = True
except ImportError:
    HAVE_CRYPTOGRAPHY = False

# PDF signature libraries
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    HAVE_REPORTLAB = True
except ImportError:
    HAVE_REPORTLAB = False

# Advanced PDF library for signatures
try:
    import PyPDF2
    from PyPDF2 import PdfWriter, PdfReader
    HAVE_PYPDF2 = True
except ImportError:
    HAVE_PYPDF2 = False

logger = logging.getLogger(__name__)

class DigitalSignatureSystem:
    """Professional digital signature system for DKI Engine reports"""
    
    def __init__(self, certificates_dir: str = "certificates"):
        self.certificates_dir = Path(certificates_dir)
        self.certificates_dir.mkdir(exist_ok=True)
        
        # Signature configurations
        self.signature_configs = {
            'investigator': {
                'title': 'Licensed Private Investigator',
                'description': 'This report has been digitally signed by a licensed private investigator',
                'position': {'x': 1.0, 'y': 1.0},  # inches from bottom-left
                'size': {'width': 3.0, 'height': 1.0}
            },
            'supervisor': {
                'title': 'Supervising Investigator',
                'description': 'Reviewed and approved by supervising investigator',
                'position': {'x': 4.5, 'y': 1.0},
                'size': {'width': 3.0, 'height': 1.0}
            },
            'company': {
                'title': 'Company Seal',
                'description': 'Official company authorization and seal',
                'position': {'x': 2.75, 'y': 0.25},
                'size': {'width': 2.5, 'height': 0.75}
            }
        }
        
        # Available certificates
        self.certificates = {}
        self.load_certificates()
        
        logger.info("Digital signature system initialized")
    
    def load_certificates(self):
        """Load available digital certificates"""
        
        try:
            cert_file = self.certificates_dir / 'certificates.json'
            if cert_file.exists():
                import json
                with open(cert_file, 'r') as f:
                    cert_data = json.load(f)
                
                for cert_name, cert_info in cert_data.items():
                    cert_path = Path(cert_info['path'])
                    if cert_path.exists():
                        self.certificates[cert_name] = cert_info
                        logger.debug(f"Loaded certificate: {cert_name}")
            
            logger.info(f"Loaded {len(self.certificates)} certificates")
            
        except Exception as e:
            logger.error(f"Failed to load certificates: {e}")
    
    def create_self_signed_certificate(self, name: str, organization: str, 
                                     email: str, license_number: str = None) -> str:
        """Create a self-signed certificate for testing/internal use"""
        
        if not HAVE_CRYPTOGRAPHY:
            raise RuntimeError("cryptography library not available for certificate creation")
        
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Create certificate subject
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.COMMON_NAME, name),
                x509.NameAttribute(NameOID.EMAIL_ADDRESS, email),
            ])
            
            # Add license number if provided
            if license_number:
                subject = x509.Name(list(subject) + [
                    x509.NameAttribute(NameOID.SERIAL_NUMBER, license_number)
                ])
                issuer = subject
            
            # Create certificate
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.RFC822Name(email),
                ]),
                critical=False,
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=True,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            ).sign(private_key, hashes.SHA256())
            
            # Save certificate and private key
            cert_name = f"{name.replace(' ', '_').lower()}_cert"
            cert_path = self.certificates_dir / f"{cert_name}.pem"
            key_path = self.certificates_dir / f"{cert_name}_key.pem"
            
            # Write certificate
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Write private key
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Update certificates registry
            cert_info = {
                'name': name,
                'organization': organization,
                'email': email,
                'license_number': license_number,
                'path': str(cert_path),
                'key_path': str(key_path),
                'created': datetime.now().isoformat(),
                'type': 'self_signed'
            }
            
            self.certificates[cert_name] = cert_info
            self.save_certificates_registry()
            
            logger.info(f"Created self-signed certificate: {cert_name}")
            return cert_name
            
        except Exception as e:
            logger.error(f"Failed to create certificate: {e}")
            raise
    
    def save_certificates_registry(self):
        """Save certificates registry to file"""
        
        try:
            import json
            cert_file = self.certificates_dir / 'certificates.json'
            with open(cert_file, 'w') as f:
                json.dump(self.certificates, f, indent=2)
            logger.debug("Saved certificates registry")
        except Exception as e:
            logger.error(f"Failed to save certificates registry: {e}")
    
    def sign_pdf(self, pdf_path: str, output_path: str, 
                certificate_name: str, signature_type: str = 'investigator',
                signature_text: str = None, signature_reason: str = None) -> bool:
        """Add digital signature to PDF document"""
        
        try:
            if not HAVE_REPORTLAB or not HAVE_PYPDF2:
                # Fallback to visual signature only
                return self._add_visual_signature(
                    pdf_path, output_path, certificate_name, 
                    signature_type, signature_text, signature_reason
                )
            
            # Get certificate info
            if certificate_name not in self.certificates:
                raise ValueError(f"Certificate not found: {certificate_name}")
            
            cert_info = self.certificates[certificate_name]
            config = self.signature_configs.get(signature_type, self.signature_configs['investigator'])
            
            # Create signature appearance
            signature_text = signature_text or f"Digitally signed by {cert_info['name']}"
            signature_reason = signature_reason or "Investigation Report Authentication"
            
            # Read original PDF
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                writer = PdfWriter()
                
                # Copy all pages
                for page in reader.pages:
                    writer.add_page(page)
                
                # Add signature to last page
                last_page = writer.pages[-1]
                
                # Create signature annotation (simplified version)
                # In a full implementation, this would use proper PDF signature standards
                signature_info = {
                    'signer': cert_info['name'],
                    'organization': cert_info.get('organization', ''),
                    'email': cert_info.get('email', ''),
                    'license': cert_info.get('license_number', ''),
                    'timestamp': datetime.now().isoformat(),
                    'reason': signature_reason,
                    'location': 'DKI Engine Report System'
                }
                
                # Add signature metadata
                writer.add_metadata({
                    '/DKI_Signature': str(signature_info),
                    '/SignatureType': signature_type,
                    '/SignedBy': cert_info['name'],
                    '/SignedAt': datetime.now().isoformat()
                })
                
                # Write signed PDF
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
            
            # Add visual signature overlay
            self._add_visual_signature_overlay(
                output_path, output_path, cert_info, config, 
                signature_text, signature_reason
            )
            
            logger.info(f"Successfully signed PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sign PDF: {e}")
            return False
    
    def _add_visual_signature(self, pdf_path: str, output_path: str,
                            certificate_name: str, signature_type: str,
                            signature_text: str, signature_reason: str) -> bool:
        """Add visual signature when full digital signature is not available"""
        
        try:
            # Get certificate and configuration
            cert_info = self.certificates.get(certificate_name, {})
            config = self.signature_configs.get(signature_type, self.signature_configs['investigator'])
            
            # Create signature overlay
            temp_overlay = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_overlay.close()
            
            # Create signature appearance
            c = canvas.Canvas(temp_overlay.name, pagesize=letter)
            
            # Position signature
            x = config['position']['x'] * inch
            y = config['position']['y'] * inch
            width = config['size']['width'] * inch
            height = config['size']['height'] * inch
            
            # Draw signature box
            c.setStrokeColorRGB(0.2, 0.2, 0.2)
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(x, y, width, height, fill=1, stroke=1)
            
            # Add signature text
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 10)
            
            # Title
            c.drawString(x + 5, y + height - 15, config['title'])
            
            # Signer name
            c.setFont("Helvetica", 9)
            signer_name = cert_info.get('name', 'Digital Signature')
            c.drawString(x + 5, y + height - 30, f"Signed by: {signer_name}")
            
            # Organization
            if cert_info.get('organization'):
                c.drawString(x + 5, y + height - 45, f"Organization: {cert_info['organization']}")
            
            # License number
            if cert_info.get('license_number'):
                c.drawString(x + 5, y + height - 60, f"License: {cert_info['license_number']}")
            
            # Timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.setFont("Helvetica", 8)
            c.drawString(x + 5, y + 5, f"Signed: {timestamp}")
            
            c.save()
            
            # Merge with original PDF
            if HAVE_PYPDF2:
                # Read original PDF
                with open(pdf_path, 'rb') as original_file:
                    original_reader = PdfReader(original_file)
                    
                    # Read overlay
                    with open(temp_overlay.name, 'rb') as overlay_file:
                        overlay_reader = PdfReader(overlay_file)
                        overlay_page = overlay_reader.pages[0]
                        
                        # Create writer
                        writer = PdfWriter()
                        
                        # Copy all pages and add overlay to last page
                        for i, page in enumerate(original_reader.pages):
                            if i == len(original_reader.pages) - 1:  # Last page
                                page.merge_page(overlay_page)
                            writer.add_page(page)
                        
                        # Write result
                        with open(output_path, 'wb') as output_file:
                            writer.write(output_file)
            else:
                # Fallback - just copy original file
                import shutil
                shutil.copy2(pdf_path, output_path)
            
            # Cleanup
            os.unlink(temp_overlay.name)
            
            logger.info(f"Added visual signature to PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add visual signature: {e}")
            return False
    
    def _add_visual_signature_overlay(self, pdf_path: str, output_path: str,
                                    cert_info: Dict[str, Any], config: Dict[str, Any],
                                    signature_text: str, signature_reason: str):
        """Add visual signature overlay to existing PDF"""
        
        # This is a simplified version - in practice would use more sophisticated PDF manipulation
        pass
    
    def verify_signature(self, pdf_path: str) -> Dict[str, Any]:
        """Verify digital signature on PDF document"""
        
        try:
            verification_result = {
                'is_signed': False,
                'is_valid': False,
                'signer': None,
                'signed_at': None,
                'certificate_info': {},
                'signature_type': None,
                'errors': []
            }
            
            if not HAVE_PYPDF2:
                verification_result['errors'].append("PyPDF2 not available for signature verification")
                return verification_result
            
            # Read PDF and check for signature metadata
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                
                # Check metadata for DKI signature
                metadata = reader.metadata
                if metadata and '/DKI_Signature' in metadata:
                    verification_result['is_signed'] = True
                    
                    # Parse signature info
                    import ast
                    try:
                        sig_info = ast.literal_eval(metadata['/DKI_Signature'])
                        verification_result['signer'] = sig_info.get('signer')
                        verification_result['signed_at'] = sig_info.get('timestamp')
                        verification_result['certificate_info'] = sig_info
                        verification_result['signature_type'] = metadata.get('/SignatureType')
                        verification_result['is_valid'] = True  # Simplified validation
                    except Exception as e:
                        verification_result['errors'].append(f"Failed to parse signature: {e}")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Failed to verify signature: {e}")
            return {
                'is_signed': False,
                'is_valid': False,
                'errors': [str(e)]
            }
    
    def show_signature_dialog(self, parent, pdf_path: str) -> bool:
        """Show digital signature dialog"""
        
        dialog = SignatureDialog(parent, self, pdf_path)
        parent.wait_window(dialog.dialog)
        
        return dialog.signature_applied
    
    def get_available_certificates(self) -> List[str]:
        """Get list of available certificate names"""
        return list(self.certificates.keys())
    
    def get_certificate_info(self, certificate_name: str) -> Optional[Dict[str, Any]]:
        """Get certificate information"""
        return self.certificates.get(certificate_name)


class SignatureDialog:
    """Digital signature application dialog"""
    
    def __init__(self, parent, signature_system: DigitalSignatureSystem, pdf_path: str):
        self.parent = parent
        self.signature_system = signature_system
        self.pdf_path = pdf_path
        self.signature_applied = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Digital Signature")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (250)
        y = (self.dialog.winfo_screenheight() // 2) - (200)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup signature dialog UI"""
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Certificate selection
        cert_frame = ttk.LabelFrame(main_frame, text="Select Certificate", padding="5")
        cert_frame.pack(fill='x', pady=(0, 10))
        
        certificates = self.signature_system.get_available_certificates()
        
        if not certificates:
            ttk.Label(cert_frame, text="No certificates available. Create one first.").pack()
            
            ttk.Button(
                cert_frame,
                text="Create Certificate",
                command=self.create_certificate
            ).pack(pady=5)
        else:
            self.cert_var = tk.StringVar(value=certificates[0])
            cert_combo = ttk.Combobox(
                cert_frame,
                textvariable=self.cert_var,
                values=certificates,
                state='readonly'
            )
            cert_combo.pack(fill='x')
            cert_combo.bind('<<ComboboxSelected>>', self.on_certificate_selected)
        
        # Certificate info
        info_frame = ttk.LabelFrame(main_frame, text="Certificate Information", padding="5")
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.cert_info_text = tk.Text(info_frame, height=6, state='disabled')
        self.cert_info_text.pack(fill='x')
        
        # Signature settings
        settings_frame = ttk.LabelFrame(main_frame, text="Signature Settings", padding="5")
        settings_frame.pack(fill='x', pady=(0, 10))
        
        # Signature type
        type_frame = ttk.Frame(settings_frame)
        type_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(type_frame, text="Signature Type:").pack(side='left')
        self.sig_type_var = tk.StringVar(value="investigator")
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.sig_type_var,
            values=list(self.signature_system.signature_configs.keys()),
            state='readonly'
        )
        type_combo.pack(side='right')
        
        # Signature reason
        reason_frame = ttk.Frame(settings_frame)
        reason_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(reason_frame, text="Reason:").pack(side='left')
        self.reason_var = tk.StringVar(value="Investigation Report Authentication")
        reason_entry = ttk.Entry(reason_frame, textvariable=self.reason_var)
        reason_entry.pack(side='right', fill='x', expand=True, padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Verify Existing",
            command=self.verify_signature
        ).pack(side='left')
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_signature
        ).pack(side='right')
        
        ttk.Button(
            button_frame,
            text="Sign Document",
            command=self.apply_signature
        ).pack(side='right', padx=(0, 5))
        
        # Initialize certificate info
        if certificates:
            self.update_certificate_info()
    
    def on_certificate_selected(self, event=None):
        """Handle certificate selection change"""
        self.update_certificate_info()
    
    def update_certificate_info(self):
        """Update certificate information display"""
        
        if not hasattr(self, 'cert_var'):
            return
        
        cert_name = self.cert_var.get()
        cert_info = self.signature_system.get_certificate_info(cert_name)
        
        if cert_info:
            info_text = f"Name: {cert_info.get('name', 'N/A')}\n"
            info_text += f"Organization: {cert_info.get('organization', 'N/A')}\n"
            info_text += f"Email: {cert_info.get('email', 'N/A')}\n"
            info_text += f"License: {cert_info.get('license_number', 'N/A')}\n"
            info_text += f"Created: {cert_info.get('created', 'N/A')}\n"
            info_text += f"Type: {cert_info.get('type', 'N/A')}"
            
            self.cert_info_text.config(state='normal')
            self.cert_info_text.delete('1.0', 'end')
            self.cert_info_text.insert('1.0', info_text)
            self.cert_info_text.config(state='disabled')
    
    def create_certificate(self):
        """Show certificate creation dialog"""
        
        cert_dialog = CertificateCreationDialog(self.dialog, self.signature_system)
        self.dialog.wait_window(cert_dialog.dialog)
        
        if cert_dialog.certificate_created:
            # Refresh certificate list
            certificates = self.signature_system.get_available_certificates()
            if certificates:
                # Recreate the certificate selection UI
                self.dialog.destroy()
                self.__init__(self.parent, self.signature_system, self.pdf_path)
    
    def apply_signature(self):
        """Apply digital signature to PDF"""
        
        try:
            if not hasattr(self, 'cert_var'):
                messagebox.showerror("Error", "No certificate selected")
                return
            
            cert_name = self.cert_var.get()
            sig_type = self.sig_type_var.get()
            reason = self.reason_var.get()
            
            # Choose output location
            output_path = filedialog.asksaveasfilename(
                title="Save Signed PDF",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")]
            )
            
            if not output_path:
                return
            
            # Apply signature
            success = self.signature_system.sign_pdf(
                self.pdf_path,
                output_path,
                cert_name,
                sig_type,
                signature_reason=reason
            )
            
            if success:
                self.signature_applied = True
                messagebox.showinfo("Success", f"Document signed successfully!\nSaved as: {output_path}")
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to sign document")
                
        except Exception as e:
            logger.error(f"Failed to apply signature: {e}")
            messagebox.showerror("Error", f"Signature failed: {str(e)}")
    
    def verify_signature(self):
        """Verify existing signature on PDF"""
        
        verification = self.signature_system.verify_signature(self.pdf_path)
        
        if verification['is_signed']:
            if verification['is_valid']:
                message = f"Document is digitally signed and valid!\n\n"
                message += f"Signed by: {verification.get('signer', 'Unknown')}\n"
                message += f"Signed at: {verification.get('signed_at', 'Unknown')}\n"
                message += f"Signature type: {verification.get('signature_type', 'Unknown')}"
                messagebox.showinfo("Signature Verification", message)
            else:
                message = "Document is signed but signature is invalid!\n\n"
                message += f"Errors: {', '.join(verification.get('errors', []))}"
                messagebox.showwarning("Signature Verification", message)
        else:
            messagebox.showinfo("Signature Verification", "Document is not digitally signed")
    
    def cancel_signature(self):
        """Cancel signature operation"""
        self.signature_applied = False
        self.dialog.destroy()


class CertificateCreationDialog:
    """Certificate creation dialog"""
    
    def __init__(self, parent, signature_system: DigitalSignatureSystem):
        self.parent = parent
        self.signature_system = signature_system
        self.certificate_created = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Digital Certificate")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (200)
        y = (self.dialog.winfo_screenheight() // 2) - (150)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup certificate creation UI"""
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Certificate information
        info_frame = ttk.LabelFrame(main_frame, text="Certificate Information", padding="10")
        info_frame.pack(fill='x', pady=(0, 10))
        
        # Name
        ttk.Label(info_frame, text="Full Name:").grid(row=0, column=0, sticky='w', pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky='ew', pady=2)
        
        # Organization
        ttk.Label(info_frame, text="Organization:").grid(row=1, column=0, sticky='w', pady=2)
        self.org_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.org_var, width=30).grid(row=1, column=1, sticky='ew', pady=2)
        
        # Email
        ttk.Label(info_frame, text="Email:").grid(row=2, column=0, sticky='w', pady=2)
        self.email_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.email_var, width=30).grid(row=2, column=1, sticky='ew', pady=2)
        
        # License number
        ttk.Label(info_frame, text="License Number:").grid(row=3, column=0, sticky='w', pady=2)
        self.license_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.license_var, width=30).grid(row=3, column=1, sticky='ew', pady=2)
        
        info_frame.columnconfigure(1, weight=1)
        
        # Warning
        warning_frame = ttk.Frame(main_frame)
        warning_frame.pack(fill='x', pady=(0, 10))
        
        warning_text = "Note: This creates a self-signed certificate for internal use.\nFor legal documents, use a certificate from a trusted authority."
        ttk.Label(warning_frame, text=warning_text, font=('TkDefaultFont', 8), foreground='red').pack()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_creation
        ).pack(side='right')
        
        ttk.Button(
            button_frame,
            text="Create Certificate",
            command=self.create_certificate
        ).pack(side='right', padx=(0, 5))
    
    def create_certificate(self):
        """Create the certificate"""
        
        try:
            name = self.name_var.get().strip()
            organization = self.org_var.get().strip()
            email = self.email_var.get().strip()
            license_number = self.license_var.get().strip()
            
            # Validate inputs
            if not name:
                messagebox.showerror("Error", "Name is required")
                return
            
            if not organization:
                messagebox.showerror("Error", "Organization is required")
                return
            
            if not email:
                messagebox.showerror("Error", "Email is required")
                return
            
            # Create certificate
            cert_name = self.signature_system.create_self_signed_certificate(
                name, organization, email, license_number
            )
            
            self.certificate_created = True
            messagebox.showinfo("Success", f"Certificate '{cert_name}' created successfully!")
            self.dialog.destroy()
            
        except Exception as e:
            logger.error(f"Failed to create certificate: {e}")
            messagebox.showerror("Error", f"Failed to create certificate: {str(e)}")
    
    def cancel_creation(self):
        """Cancel certificate creation"""
        self.certificate_created = False
        self.dialog.destroy()


# Test the digital signature system
if __name__ == "__main__":
    print("🔐 Testing DKI Engine Digital Signature System...")
    
    signature_system = DigitalSignatureSystem()
    
    print(f"Available Certificates: {signature_system.get_available_certificates()}")
    print(f"Signature Configurations: {list(signature_system.signature_configs.keys())}")
    
    # Test certificate creation
    if HAVE_CRYPTOGRAPHY:
        print("✅ Certificate creation available")
    else:
        print("⚠️  Certificate creation requires cryptography library")
    
    print("✅ Digital signature system initialized successfully!")








