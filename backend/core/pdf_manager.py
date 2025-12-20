"""
PDF Manager - Handles PDF generation from HTML templates
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class PDFManager:
    """Manages PDF generation using Jinja2 templates and WeasyPrint"""

    PROJECT_ROOT = Path(__file__).parent.parent.parent
    TEMPLATES_DIR = PROJECT_ROOT / "templates"
    OUTPUT_DIR = PROJECT_ROOT / "output"

    @staticmethod
    def ensure_output_dir():
        """Create output directory if it doesn't exist"""
        PDFManager.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_font_size(text: str) -> int:
        """
        Returns font size based on text length to prevent line wrapping
        Scales down font size progressively for longer names
        """
        text_len = len(text)
        if text_len <= 15:
            return 20
        if text_len <= 20:
            return 18
        if text_len <= 25:
            return 16
        if text_len <= 30:
            return 14
        return 12

    @staticmethod
    def annotate_font_sizes(payload: dict[str, Any]):
        """Add font-size hints to each report payload for the template"""
        def apply(record: dict[str, Any]):
            record['student_name_font_size'] = PDFManager.get_font_size(record.get('student_name', ''))
            record['father_name_font_size'] = PDFManager.get_font_size(record.get('father_name', ''))

        records = payload.get('records')
        if isinstance(records, list):
            for record in records:
                apply(record)
        else:
            apply(payload)

    @staticmethod
    def render_template(
        data: dict[str, Any],
        template_name: str = 'report_card.html',
        asset_base: str | None = None,
        css_name: str = 'styles.css',
    ):
        """
        Render HTML template with student data using Jinja2

        Args:
            data (dict): Dictionary containing payload for the template
            template_name (str): Template filename to render

        Returns:
            str: Rendered HTML content
        """
        try:
            PDFManager.annotate_font_sizes(data)

            css_path = PDFManager.TEMPLATES_DIR / css_name
            with open(css_path, 'r', encoding='utf-8') as handle:
                css_content = handle.read()

            templates_dir_str = str(PDFManager.TEMPLATES_DIR).replace('\\', '/')
            if asset_base:
                css_content = css_content.replace("url('Revue.ttf')", f"url('{asset_base}/Revue.ttf')")
                css_content = css_content.replace("url('calibri-regular.ttf')", f"url('{asset_base}/calibri-regular.ttf')")
                css_content = css_content.replace("url('calibri-italic.ttf')", f"url('{asset_base}/calibri-italic.ttf')")
            else:
                css_content = css_content.replace("url('Revue.ttf')", f"url('file:///{templates_dir_str}/Revue.ttf')")
                css_content = css_content.replace("url('calibri-regular.ttf')", f"url('file:///{templates_dir_str}/calibri-regular.ttf')")
                css_content = css_content.replace("url('calibri-italic.ttf')", f"url('file:///{templates_dir_str}/calibri-italic.ttf')")

            env = Environment(loader=FileSystemLoader(str(PDFManager.TEMPLATES_DIR)))
            template = env.get_template(template_name)

            context: dict[str, Any] = dict(data)
            context['css_content'] = css_content
            context['template_dir'] = templates_dir_str
            context['report'] = data
            context['template_asset_base'] = asset_base

            html_content = template.render(**context)
            return html_content

        except Exception as exc:  # pragma: no cover
            raise Exception(f"Error rendering template: {exc}") from exc

    @staticmethod
    def generate_pdf(
        filename: str,
        data: dict[str, Any],
        template_name: str = 'report_card.html',
        css_name: str = 'styles.css',
    ):
        """
        Generate PDF from HTML template

        Args:
            filename (str): Base name for the PDF file
            data (dict): Dictionary with payload data
            template_name (str): Template filename to render

        Returns:
            tuple: (success: bool, message: str, pdf_path: str or None)
        """
        try:
            from weasyprint import HTML

            PDFManager.ensure_output_dir()
            html_content = PDFManager.render_template(data, template_name, css_name=css_name)

            temp_html = PDFManager.OUTPUT_DIR / "temp_report.html"
            with open(temp_html, 'w', encoding='utf-8') as handle:
                handle.write(html_content)

            pdf_filename = f"{filename}.pdf"
            pdf_path = PDFManager.OUTPUT_DIR / pdf_filename

            HTML(str(temp_html)).write_pdf(str(pdf_path))
            temp_html.unlink()

            return True, "PDF created successfully!", str(pdf_path)

        except ImportError:
            return False, "WeasyPrint not installed. Run: pip install weasyprint", None
        except Exception as exc:  # pragma: no cover
            return False, f"Error generating PDF: {exc}", None
