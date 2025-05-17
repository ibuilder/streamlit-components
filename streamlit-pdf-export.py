import streamlit as st
import base64
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import os

class PDFExporter:
    """
    A Streamlit component for exporting page content to PDF and appending 
    any uploaded PDF attachments.
    """
    
    def __init__(self, title="Export to PDF"):
        """
        Initialize the PDF Exporter component.
        
        Args:
            title (str): The title for the export button.
        """
        self.title = title
        self.attachments = []
        
    def render_ui(self):
        """Render the UI components for the PDF exporter."""
        st.subheader("PDF Export Options")
        
        # File uploader for PDF attachments
        uploaded_files = st.file_uploader(
            "Upload PDF attachments to append", 
            type="pdf", 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            self.attachments = uploaded_files
            st.success(f"{len(uploaded_files)} PDF(s) uploaded successfully.")
            
            # Show attachment previews
            if st.checkbox("Preview attachments"):
                for i, pdf_file in enumerate(self.attachments):
                    with st.expander(f"Attachment {i+1}: {pdf_file.name}"):
                        # Display first page as preview
                        try:
                            pdf_bytes = pdf_file.read()
                            pdf_file.seek(0)  # Reset to beginning for later use
                            reader = PdfReader(io.BytesIO(pdf_bytes))
                            num_pages = len(reader.pages)
                            st.write(f"Pages: {num_pages}")
                            # Use PDF display object if you want to show actual content
                            # Here we just show the file details
                        except Exception as e:
                            st.error(f"Error reading PDF: {e}")
        
        # Export button
        export_btn = st.button(self.title)
        if export_btn:
            return True
        return False
    
    def export_to_pdf(self, content, filename="export.pdf"):
        """
        Export content to PDF and append attachments.
        
        Args:
            content (dict): Dictionary with content elements to include in the PDF.
                Format: {"title": str, "text": str, "tables": [pandas.DataFrame], ...}
            filename (str): Output filename for the PDF.
            
        Returns:
            bytes: The generated PDF as bytes.
        """
        # Create a temporary file to store the main content PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_path = tmp_file.name
        
        # Generate the main content PDF
        self._generate_content_pdf(content, tmp_path)
        
        # Merge the main content with attachments
        merged_pdf_bytes = self._merge_pdfs(tmp_path)
        
        # Clean up the temporary file
        os.unlink(tmp_path)
        
        # Create a download link for the PDF
        self._create_download_link(merged_pdf_bytes, filename)
        
        return merged_pdf_bytes
    
    def _generate_content_pdf(self, content, output_path):
        """Generate a PDF with the main content."""
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add title
        if "title" in content:
            title_style = styles["Title"]
            elements.append(Paragraph(content["title"], title_style))
            elements.append(Spacer(1, 12))
        
        # Add main text
        if "text" in content:
            text_style = styles["Normal"]
            text_paragraphs = content["text"].split('\n')
            for paragraph in text_paragraphs:
                if paragraph.strip():
                    elements.append(Paragraph(paragraph, text_style))
                    elements.append(Spacer(1, 6))
        
        # Add tables if present
        if "tables" in content and content["tables"]:
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors
            
            for df in content["tables"]:
                # Convert DataFrame to a list of lists
                data = [df.columns.tolist()]  # Header row
                data.extend(df.values.tolist())  # Data rows
                
                # Create table
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                elements.append(Spacer(1, 12))
                elements.append(table)
                elements.append(Spacer(1, 12))
        
        # Add images if present
        if "images" in content and content["images"]:
            from reportlab.platypus import Image
            
            for img_data in content["images"]:
                try:
                    # img_data should be a dict with 'data' (bytes) and 'width'/'height' (optional)
                    img = Image(io.BytesIO(img_data['data']), 
                                width=img_data.get('width', 400), 
                                height=img_data.get('height', 300))
                    elements.append(img)
                    elements.append(Spacer(1, 12))
                except Exception as e:
                    st.error(f"Error adding image to PDF: {e}")
        
        # Build the PDF
        doc.build(elements)
        
        # Save to the output path
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        return output_path
    
    def _merge_pdfs(self, main_content_path):
        """Merge the main content PDF with attachment PDFs."""
        pdf_writer = PdfWriter()
        
        # Add pages from main content
        with open(main_content_path, 'rb') as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
        
        # Add a separator page if there are attachments
        if self.attachments:
            # Create a temporary file for the separator page
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                separator_path = tmp_file.name
            
            # Generate a separator page
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=letter)
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(300, 400, "ATTACHMENTS")
            c.setFont("Helvetica", 12)
            c.drawCentredString(300, 380, "The following pages contain attached documents")
            c.save()
            
            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            separator_pdf = PdfReader(packet)
            
            # Add the separator page
            pdf_writer.add_page(separator_pdf.pages[0])
            
            # Clean up
            os.unlink(separator_path)
        
        # Add each attachment
        for attachment in self.attachments:
            attachment.seek(0)  # Ensure we're at the beginning of the file
            try:
                pdf_reader = PdfReader(attachment)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
            except Exception as e:
                st.error(f"Error merging attachment {attachment.name}: {e}")
        
        # Save the result to a BytesIO object
        output_buffer = io.BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        return output_buffer.getvalue()
    
    def _create_download_link(self, pdf_bytes, filename):
        """Create a download link for the generated PDF."""
        b64_pdf = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{filename}">Download {filename}</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        # Also display success message
        st.success(f"PDF successfully generated with {len(self.attachments)} attachment(s)!")


# Example usage
if __name__ == "__main__":
    st.title("PDF Export Component Demo")
    
    # Main content
    st.write("This is a demonstration of the PDF export component.")
    st.write("Enter some text below that will be included in the PDF:")
    
    user_text = st.text_area("Text for PDF", height=200,
                            value="This is sample text that will be included in the exported PDF.\n\n"
                                  "You can add multiple paragraphs and they will be formatted properly in the PDF.")
    
    # Optional: Add a sample table
    import pandas as pd
    import numpy as np
    
    if st.checkbox("Include sample table"):
        df = pd.DataFrame(
            np.random.randn(5, 3),
            columns=('Col %d' % i for i in range(3)),
            index=('Row %d' % i for i in range(5))
        )
        st.dataframe(df)
    else:
        df = None
    
    # Create the PDF exporter
    pdf_exporter = PDFExporter("Generate and Download PDF")
    
    # Render the UI
    if pdf_exporter.render_ui():
        # Prepare content for the PDF
        content = {
            "title": "Sample PDF Export",
            "text": user_text,
        }
        
        # Add table if included
        if df is not None:
            content["tables"] = [df]
        
        # Generate and offer the PDF for download
        pdf_exporter.export_to_pdf(content, "streamlit_export.pdf")
