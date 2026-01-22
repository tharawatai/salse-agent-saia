"""
SAIA Insurance Broker Platform - PDF Generator Service
خدمة توليد ملفات PDF للفاتورة ووثيقة التأمين
يستخدم Playwright (Chromium) للحصول على أفضل جودة مع دعم RTL والخطوط العربية
"""
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import base64

logger = logging.getLogger(__name__)

# المسارات الأساسية
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
LOGOS_DIR = STATIC_DIR / "logos"
OUTPUT_DIR = Path("/tmp/saia_documents")

# Windows fix
if os.name == 'nt':
    OUTPUT_DIR = Path(os.environ.get('TEMP', 'C:/temp')) / "saia_documents"

try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


class PDFGenerator:
    """
    مولد PDF باستخدام Playwright (Chromium Headless)
    يدعم CSS الحديثة، RTL، والخطوط العربية بشكل ممتاز
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._ensure_directories()
        self._playwright_installed = None
    
    def _ensure_directories(self):
        """التأكد من وجود المجلدات المطلوبة"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def _check_playwright(self) -> bool:
        """التحقق من تثبيت Playwright"""
        if self._playwright_installed is not None:
            return self._playwright_installed
        try:
            import playwright
            self._playwright_installed = True
        except ImportError:
            self._playwright_installed = False
            self.logger.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return self._playwright_installed
    
    def _load_template(self, template_name: str) -> str:
        """تحميل قالب HTML"""
        template_path = TEMPLATES_DIR / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text(encoding='utf-8')
    
    def _get_logo_base64(self, logo_name: str, max_size_kb: int = 300) -> str:
        """تحويل الشعار لـ Base64"""
        logo_path = LOGOS_DIR / logo_name
        if logo_path.exists():
            file_size_kb = logo_path.stat().st_size / 1024
            if file_size_kb > max_size_kb:
                self.logger.warning(f"Logo {logo_name} too large: {file_size_kb:.0f}KB")
                return ""
            with open(logo_path, 'rb') as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        self.logger.debug(f"Logo not found: {logo_path}")
        return ""
    
    def _generate_qr_code(self, data: Dict[str, Any]) -> str:
        """توليد QR Code ديناميكي من بيانات الفاتورة"""
        try:
            import qrcode
            from io import BytesIO
            
            # بناء نص QR Code
            qr_data = f"""SAIA Invoice
Invoice: {data.get('invoice_number', 'N/A')}
Date: {data.get('issue_date', 'N/A')}
Amount: {data.get('total_amount', '0')} SAR
ID: {data.get('national_id', 'N/A')}
Sadad: {data.get('sadad_number', 'N/A')}"""
            
            # إنشاء QR Code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=2,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # تحويل لصورة
            img = qr.make_image(fill_color="black", back_color="white")
            
            # تحويل لـ Base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode()}"
            
        except Exception as e:
            self.logger.error(f"QR Code generation failed: {e}")
            return ""
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """تعبئة القالب بالبيانات"""
        # إضافة الشعارات
        data['saia_logo'] = self._get_logo_base64('saia_logo.png')
        data['bineyes_logo'] = self._get_logo_base64('bineyes_logo.png')
        
        # توليد QR Code ديناميكي
        data['qr_code'] = self._generate_qr_code(data)
        
        # استبدال المتغيرات في القالب
        for key, value in data.items():
            template = template.replace(f"{{{{ {key} }}}}", str(value) if value else '')
        
        return template
    
    def _html_to_pdf_playwright(self, html_content: str, output_path: str) -> bool:
        """
        تحويل HTML إلى PDF باستخدام Playwright
        يدعم كلاً من sync و async contexts
        """
        try:
            # التحقق من وجود event loop نشط
            try:
                loop = asyncio.get_running_loop()
                is_async = True
            except RuntimeError:
                is_async = False
            
            if is_async:
                # استخدام Async API
                return asyncio.get_event_loop().run_until_complete(
                    self._html_to_pdf_playwright_async(html_content, output_path)
                )
            else:
                # استخدام Sync API
                return self._html_to_pdf_playwright_sync(html_content, output_path)
                
        except Exception as e:
            self.logger.error(f"❌ Playwright PDF generation failed: {e}")
            return False
    
    def _html_to_pdf_playwright_sync(self, html_content: str, output_path: str) -> bool:
        """Sync version of Playwright PDF generation"""
        try:
            from playwright.sync_api import sync_playwright
            
            self.logger.info(f"🚀 Starting Playwright PDF generation (sync)...")
            
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_content(html_content, wait_until="load")
                page.pdf(
                    path=output_path,
                    format="A4",
                    print_background=True,
                    margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"}
                )
                browser.close()
            
            self.logger.info(f"✅ PDF generated: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Sync Playwright failed: {e}")
            return False
    
    async def _html_to_pdf_playwright_async(self, html_content: str, output_path: str) -> bool:
        """Async version of Playwright PDF generation"""
        try:
            from playwright.async_api import async_playwright
            
            self.logger.info(f"🚀 Starting Playwright PDF generation (async)...")
            
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_content(html_content, wait_until="load")
                await page.pdf(
                    path=output_path,
                    format="A4",
                    print_background=True,
                    margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"}
                )
                await browser.close()
            
            self.logger.info(f"✅ PDF generated: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Async Playwright failed: {e}")
            return False
    
    def generate_invoice_html(self, context_data: Dict[str, Any]) -> str:
        """توليد HTML للفاتورة"""
        today = datetime.now()
        next_year = today + timedelta(days=365)
        
        vehicle_info = self._get_vehicle_info(context_data)
        
        data = {
            'invoice_number': context_data.get('invoice_id', f"INV-{today.strftime('%Y%m%d%H%M%S')}"),
            'issue_date': today.strftime('%Y-%m-%d'),
            'sadad_number': context_data.get('sadad_number', f"177{today.strftime('%Y%m%d%H%M%S')}"),
            'national_id': context_data.get('national_id', 'غير محدد'),
            'birth_date': context_data.get('birth_date', 'غير محدد'),
            'phone': context_data.get('phone', 'غير محدد'),
            'total_amount': f"{context_data.get('total_amount', 0):,.2f}",
            'coverage_type': context_data.get('coverage_type', 'تأمين شامل'),
            'vehicle_info': vehicle_info,
            'plate_no': context_data.get('plate_no', 'غير محدد'),
            'company_name': context_data.get('company_name', 'شركة التأمين'),
            'policy_start': today.strftime('%Y-%m-%d'),
            'policy_end': next_year.strftime('%Y-%m-%d'),
        }
        
        # استخدام قالب PDF المبسط
        try:
            template = self._load_template('invoice_pdf.html')
        except FileNotFoundError:
            template = self._load_template('invoice.html')
        return self._render_template(template, data)
    
    def generate_policy_html(self, context_data: Dict[str, Any]) -> str:
        """توليد HTML لوثيقة التأمين"""
        today = datetime.now()
        next_year = today + timedelta(days=365)
        
        raw_vehicle_value = context_data.get('vehicle_value', 0)
        try:
            vehicle_value_num = int(float(str(raw_vehicle_value).replace(',', ''))) if raw_vehicle_value else 0
            vehicle_value_formatted = f"{vehicle_value_num:,}" if vehicle_value_num else "غير محدد"
        except (ValueError, TypeError):
            vehicle_value_formatted = str(raw_vehicle_value)
        
        raw_total = context_data.get('total_amount', 0)
        try:
            total_num = float(raw_total) if raw_total else 0
            total_formatted = f"{total_num:,.2f}" if total_num else "0.00"
        except (ValueError, TypeError):
            total_formatted = str(raw_total)
        
        data = {
            'policy_number': context_data.get('policy_id', f"POL-{today.strftime('%Y%m%d%H%M%S')}"),
            'issue_date': today.strftime('%Y-%m-%d'),
            'expiry_date': next_year.strftime('%Y-%m-%d'),
            'national_id': context_data.get('national_id', 'غير محدد'),
            'birth_date': context_data.get('birth_date', 'غير محدد'),
            'phone': context_data.get('phone', 'غير محدد'),
            'invoice_number': context_data.get('invoice_id', 'غير محدد'),
            'vehicle_brand': context_data.get('vehicle_brand', 'غير محدد'),
            'vehicle_model': context_data.get('vehicle_model', 'غير محدد'),
            'vehicle_year': context_data.get('vehicle_year', 'غير محدد'),
            'plate_no': context_data.get('plate_no', 'غير محدد'),
            'vehicle_value': vehicle_value_formatted,
            'coverage_type': context_data.get('coverage_type', 'تأمين شامل'),
            'company_name': context_data.get('company_name', 'شركة التأمين'),
            'offer_code': context_data.get('offer_code', 'N/A'),
            'premium': total_formatted,
        }
        
        # استخدام قالب PDF المبسط
        try:
            template = self._load_template('policy_pdf.html')
        except FileNotFoundError:
            template = self._load_template('policy.html')
        return self._render_template(template, data)
    
    def _html_to_pdf_weasyprint(self, html_content: str, output_path: str) -> bool:
        """تحويل HTML إلى PDF باستخدام WeasyPrint - يدعم العربية"""
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            self.logger.info("🚀 Generating PDF with WeasyPrint...")
            
            font_config = FontConfiguration()
            html = HTML(string=html_content)
            html.write_pdf(output_path, font_config=font_config)
            
            self.logger.info(f"✅ PDF generated with WeasyPrint: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ WeasyPrint failed: {e}")
            return False
    
    def _html_to_pdf_xhtml2pdf(self, html_content: str, output_path: str) -> bool:
        """تحويل HTML إلى PDF باستخدام xhtml2pdf مع دعم العربية"""
        try:
            from xhtml2pdf import pisa
            from io import BytesIO
            
            # تسجيل الخط العربي
            try:
                from xhtml2pdf.default import DEFAULT_FONT
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                
                # محاولة تسجيل خط عربي
                arabic_fonts = [
                    ('Arabic', str(STATIC_DIR / 'fonts' / 'arabtype.ttf')),
                    ('Arabic', str(STATIC_DIR / 'fonts' / 'arial.ttf')),
                    ('Arabic', 'C:/Windows/Fonts/arial.ttf'),
                    ('Arabic', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
                ]
                
                font_registered = False
                for font_name, font_path in arabic_fonts:
                    try:
                        if Path(font_path).exists():
                            pdfmetrics.registerFont(TTFont(font_name, font_path))
                            font_registered = True
                            self.logger.info(f"✅ Registered Arabic font: {font_path}")
                            break
                    except Exception as e:
                        continue
                
                if not font_registered:
                    self.logger.warning("⚠️ No Arabic font found, using default")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Font registration failed: {e}")
            
            # إنشاء PDF
            with open(output_path, 'wb') as pdf_file:
                pisa_status = pisa.CreatePDF(
                    html_content,
                    dest=pdf_file,
                    encoding='utf-8'
                )
            
            if pisa_status.err:
                self.logger.error(f"xhtml2pdf errors: {pisa_status.err}")
                return False
            
            self.logger.info(f"✅ PDF generated with xhtml2pdf: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ xhtml2pdf failed: {e}")
            return False
    
    def save_invoice_html(self, context_data: Dict[str, Any]) -> str:
        """حفظ الفاتورة كملف HTML (يمكن طباعته كـ PDF من المتصفح)"""
        invoice_id = context_data.get('invoice_id', datetime.now().strftime('%Y%m%d%H%M%S'))
        html = self.generate_invoice_html(context_data)
        
        # حفظ كـ HTML (أفضل دعم للعربية)
        html_filename = f"invoice_{invoice_id}.html"
        html_filepath = OUTPUT_DIR / html_filename
        html_filepath.write_text(html, encoding='utf-8')
        
        self.logger.info(f"✅ Invoice HTML saved: {html_filepath}")
        return str(html_filepath)
    
    def save_policy_html(self, context_data: Dict[str, Any]) -> str:
        """حفظ الوثيقة كملف PDF"""
        policy_id = context_data.get('policy_id', datetime.now().strftime('%Y%m%d%H%M%S'))
        html = self.generate_policy_html(context_data)
        
        # محاولة توليد PDF
        pdf_filename = f"policy_{policy_id}.pdf"
        pdf_filepath = OUTPUT_DIR / pdf_filename
        
        if self._html_to_pdf_xhtml2pdf(html, str(pdf_filepath)):
            return str(pdf_filepath)
        
        # Fallback إلى HTML
        html_filename = f"policy_{policy_id}.html"
        html_filepath = OUTPUT_DIR / html_filename
        html_filepath.write_text(html, encoding='utf-8')
        self.logger.warning(f"⚠️ Falling back to HTML: {html_filepath}")
        return str(html_filepath)
    
    def _get_vehicle_info(self, context_data: Dict[str, Any]) -> str:
        """تنسيق معلومات السيارة"""
        brand = context_data.get('vehicle_brand', '')
        model = context_data.get('vehicle_model', '')
        year = context_data.get('vehicle_year', '')
        plate = context_data.get('plate_no', '')
        
        parts = [p for p in [brand, model, str(year) if year else '', plate] if p]
        return ' - '.join(parts) if parts else 'غير محدد'
    
    def generate_documents(self, context_data: Dict[str, Any]) -> Dict[str, str]:
        """توليد كلا المستندين"""
        try:
            invoice_path = self.save_invoice_html(context_data)
            policy_path = self.save_policy_html(context_data)
            
            return {
                'invoice_path': invoice_path,
                'policy_path': policy_path,
                'success': True
            }
        except Exception as e:
            self.logger.error(f"Error generating documents: {e}")
            return {
                'invoice_path': None,
                'policy_path': None,
                'success': False,
                'error': str(e)
            }


# Singleton instance
pdf_generator = PDFGenerator()


def generate_payment_documents(context_data: Dict[str, Any]) -> Dict[str, str]:
    """دالة مساعدة لتوليد مستندات الدفع"""
    return pdf_generator.generate_documents(context_data)
