# Streamlit Components Collection

This repository contains a collection of reusable Streamlit components and utilities to enhance your Streamlit applications. These components provide additional functionality beyond Streamlit's core features, making it easier to build complex, interactive web applications.

## Components Overview

| Component | Description |
|-----------|-------------|
| [PDF Viewer](#pdf-viewer) | Advanced PDF viewer with navigation, zoom, markup, and measurement tools |
| [Conditional Forms](#conditional-forms) | Dynamic forms with fields that appear/disappear based on user inputs |
| [Elasticsearch CRUD](#elasticsearch-crud) | Dashboard for Elasticsearch database operations (Create, Read, Update, Delete) |
| [Excel Export](#excel-export) | Utility for exporting Streamlit data to Excel files |
| [IFC.js Viewer](#ifcjs-viewer) | 3D BIM model viewer with walkthrough navigation and element selection |
| [PDF Export](#pdf-export) | Export Streamlit content to PDF with optional attachments |
| [Repeatable Fields](#repeatable-fields) | Create dynamic, repeatable form field groups |
| [Signature Component](#signature-component) | Capture digital signatures with drawing or typing options |
| [Social Authentication](#social-authentication) | Authentication with social login providers and local credentials |
| [Weather App](#weather-app) | Simple weather app example showing component integration |

## Installation

```bash
pip install -r requirements.txt
```

## Components Usage

### PDF Viewer

An advanced PDF viewer component with navigation, zoom, markup, and measurement tools.

```python
import streamlit as st
from pdf_viewer import pdf_viewer

# Display a PDF file with the advanced viewer
pdf_viewer("document.pdf", width=800, height=600)
```

Features:
- Page navigation and direct page jumping
- Zoom controls with presets
- Text highlighting and annotation
- Drawing tools
- Measurement with custom scale settings

### Conditional Forms

Create dynamic forms where fields appear or disappear based on user inputs.

```python
from conditional_forms import (
    Form, FieldSet, ConditionalFieldSet, Condition,
    text_input, radio, selectbox
)

# Create a form with conditional fields
form = Form(name="example_form", title="Conditional Form Example")

# Basic information fieldset
basic_info = FieldSet(name="basic_info", title="Basic Information")
basic_info.add_field(text_input("name", "Name", required=True))
basic_info.add_field(radio("user_type", "I am a", options=["Individual", "Business"]))

# Business details shown only when user type is Business
business_details = ConditionalFieldSet(
    name="business_details",
    title="Business Details",
    conditions=[Condition("user_type", "equals", "Business")]
)
business_details.add_field(text_input("company_name", "Company Name"))

# Add fieldsets to form
form.add_fieldset(basic_info)
form.add_fieldset(business_details)

# Render the form
form_values = form.render()

# Handle submission
if form.is_submitted and form.is_valid:
    st.success("Form submitted successfully!")
    st.write(form_values)
```

### Elasticsearch CRUD

A dashboard for interacting with Elasticsearch databases.

```python
import streamlit as st
from elasticsearch_crud import ElasticsearchCRUD

# Initialize the component
es_dashboard = ElasticsearchCRUD()

# The dashboard will render UI for:
# - Connecting to Elasticsearch
# - Creating/selecting indices
# - Adding, viewing, updating, and deleting records
# - Searching with filters and sorting
```

### Excel Export

Utility for exporting DataFrames to Excel files.

```python
import streamlit as st
import pandas as pd
from excel_export import to_excel_download_button

# Create a DataFrame
df = pd.DataFrame({
    'Name': ['John', 'Anna', 'Peter', 'Linda'],
    'Age': [28, 34, 42, 37],
    'City': ['New York', 'Paris', 'Berlin', 'London']
})

# Display the DataFrame
st.dataframe(df)

# Add an Excel download button
to_excel_download_button(
    df=df,
    filename="data.xlsx",
    button_text="Download as Excel"
)
```

### IFC.js Viewer

A component for viewing IFC (Industry Foundation Classes) models in Streamlit.

```python
import streamlit as st
from ifcjs_viewer import ifcjs_viewer

# Upload an IFC file
uploaded_file = st.file_uploader("Upload IFC file", type=["ifc"])

if uploaded_file is not None:
    # Display the IFC model
    selection_info = ifcjs_viewer(ifc_file=uploaded_file.getvalue(), height=600)
    
    # Handle selection events
    if selection_info:
        st.write("Selected element:", selection_info)
```

Features:
- 3D visualization of BIM models
- Walk-through navigation (WASD keys)
- Element selection and property viewing
- Distance measurement tools

### PDF Export

Export Streamlit content to PDF with optional attachments.

```python
import streamlit as st
import pandas as pd
from pdf_export import PDFExporter

# Create some content
st.title("Report Title")
st.write("This is a sample report that will be exported to PDF.")

df = pd.DataFrame({
    'Column 1': [1, 2, 3],
    'Column 2': ['A', 'B', 'C']
})
st.dataframe(df)

# Create the PDF exporter
pdf_exporter = PDFExporter("Export to PDF")

# Render export UI (file upload for attachments, export button)
if pdf_exporter.render_ui():
    # Export content when button is clicked
    content = {
        "title": "Report Title",
        "text": "This is a sample report that will be exported to PDF.",
        "tables": [df]
    }
    pdf_exporter.export_to_pdf(content, "report.pdf")
```

### Repeatable Fields

Create dynamic, repeatable form field groups in Streamlit.

```python
import streamlit as st
from repeatable_fields import RepeatableField

# Create repeatable fields
contact_fields = RepeatableField(key_prefix="contact")

# Define how each field instance should render
def render_contact_field(field_id, index):
    st.subheader(f"Contact {index + 1}")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Name", key=f"{field_id}_name")
    with col2:
        st.text_input("Email", key=f"{field_id}_email")
    st.text_input("Phone", key=f"{field_id}_phone")

# Render the repeatable fields
contact_fields.render(render_contact_field, min_fields=1)

# Get values when needed
if st.button("Submit"):
    values = contact_fields.get_values(["name", "email", "phone"])
    st.write("Submitted contacts:", values)
```

### Signature Component

Capture digital signatures in Streamlit apps.

```python
import streamlit as st
from signature_component import SignaturePad

# Create a signature pad
signature_pad = SignaturePad()

# Render the signature pad with options
signature_pad.render(
    draw_options=True,  # Enable drawing signature
    typed_options=True,  # Enable typed signature
    signature_styles=["Cursive", "Formal", "Simple"],
    height=200
)

# Get the signature when submitted
if st.button("Submit Signature"):
    signature_image = signature_pad.get_signature_image()
    if signature_image:
        st.image(signature_image)
        # For downloading:
        # signature_pad.download_signature("signature.png")
```

### Social Authentication

Authentication with social login providers and local credentials.

```python
import streamlit as st
from social_auth import SocialAuthenticator

# Configure authentication
auth_config = {
    "credentials": {
        "usernames": {
            "johndoe": {
                "email": "john@example.com",
                "password": "$2b$12$tPaJoUQp9s7KdAF.KGyFlOANZK/ClQiSdl9Bha1JGl6iBloxOGhA."  # Hashed password
            }
        }
    },
    "social_providers": {
        "google": {
            "client_id": "your_google_client_id",
            "client_secret": "your_google_client_secret",
            "auth_url": "https://accounts.google.com/o/oauth2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
            "scope": "openid email profile",
            "id_field": "email"
        }
    }
}

# Initialize authenticator
authenticator = SocialAuthenticator(config_data=auth_config)

# Create login widget
authenticated, username, auth_source = authenticator.login()

# Check if user is authenticated
if authenticated:
    st.write(f"Welcome {username}! You are logged in via {auth_source}.")
    
    # Logout button
    if st.button("Logout"):
        authenticator.logout()
        st.rerun()
else:
    st.warning("Please login to continue")
```

### Weather App

A simple weather app demonstrating component integration.

```python
import streamlit as st
from weather_app import WeatherApp

# Initialize the weather app
weather_app = WeatherApp()

# Render the app
weather_app.render()
```

## Requirements

- Streamlit>=1.10.0
- Additional requirements vary by component (see individual component documentation)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.