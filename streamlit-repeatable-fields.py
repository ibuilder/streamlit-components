import streamlit as st
import uuid
from typing import Callable, Dict, List, Any, Optional, Union, Tuple


class RepeatableField:
    """
    A component for creating repeatable form fields in Streamlit.
    Allows users to dynamically add, remove, and manage multiple instances of any Streamlit input.
    """
    
    def __init__(self, key_prefix: str = "repeatable"):
        """
        Initialize the repeatable field component.
        
        Args:
            key_prefix: A prefix to use for the session state keys to avoid conflicts
        """
        self.key_prefix = key_prefix
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables if they don't exist"""
        if f"{self.key_prefix}_ids" not in st.session_state:
            st.session_state[f"{self.key_prefix}_ids"] = []
            st.session_state[f"{self.key_prefix}_count"] = 0
    
    def _generate_id(self) -> str:
        """Generate a unique ID for a new field instance"""
        return f"{self.key_prefix}_{uuid.uuid4().hex[:8]}"
    
    def add_field(self):
        """Add a new field instance"""
        new_id = self._generate_id()
        st.session_state[f"{self.key_prefix}_ids"].append(new_id)
        st.session_state[f"{self.key_prefix}_count"] += 1
        return new_id
    
    def remove_field(self, field_id: str):
        """Remove a field instance by ID"""
        if field_id in st.session_state[f"{self.key_prefix}_ids"]:
            st.session_state[f"{self.key_prefix}_ids"].remove(field_id)
            st.session_state[f"{self.key_prefix}_count"] -= 1
            
            # Clean up any stored values for this field
            for key in list(st.session_state.keys()):
                if key.startswith(f"{field_id}_"):
                    del st.session_state[key]
    
    def render(self, field_renderer: Callable[[str, int], Any], 
               min_fields: int = 1, 
               max_fields: Optional[int] = None,
               add_button_text: str = "Add Another",
               remove_button_text: str = "Remove"):
        """
        Render the repeatable fields.
        
        Args:
            field_renderer: A function that renders an individual field instance
                            It should accept the field_id and index as arguments
            min_fields: Minimum number of field instances (default: 1)
            max_fields: Maximum number of field instances (default: None, meaning unlimited)
            add_button_text: Text to display on the add button
            remove_button_text: Text to display on the remove button
        
        Returns:
            List of field IDs currently being displayed
        """
        # Ensure we have the minimum number of fields
        while len(st.session_state[f"{self.key_prefix}_ids"]) < min_fields:
            self.add_field()
        
        # Display each field with its own removal button
        for i, field_id in enumerate(st.session_state[f"{self.key_prefix}_ids"]):
            col1, col2 = st.columns([10, 1])
            
            with col1:
                field_renderer(field_id, i)
            
            with col2:
                # Only show remove button if we're above the minimum fields
                if len(st.session_state[f"{self.key_prefix}_ids"]) > min_fields:
                    st.button(remove_button_text, key=f"remove_{field_id}", 
                              on_click=self.remove_field, args=(field_id,))
        
        # Add button (only if we haven't reached the maximum)
        if max_fields is None or len(st.session_state[f"{self.key_prefix}_ids"]) < max_fields:
            st.button(add_button_text, key=f"{self.key_prefix}_add_button", on_click=self.add_field)
        
        return st.session_state[f"{self.key_prefix}_ids"]
    
    def get_values(self, value_keys: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """
        Get all values from the repeatable fields.
        
        Args:
            value_keys: A string or list of strings representing the keys to extract for each field.
                        For example, if you have fields with keys 'name' and 'email', 
                        you would pass ['name', 'email']
        
        Returns:
            A list of dictionaries, each containing the values for one field instance
        """
        if isinstance(value_keys, str):
            value_keys = [value_keys]
            
        values = []
        
        for field_id in st.session_state[f"{self.key_prefix}_ids"]:
            field_values = {}
            for key in value_keys:
                session_key = f"{field_id}_{key}"
                if session_key in st.session_state:
                    field_values[key] = st.session_state[session_key]
                else:
                    field_values[key] = None
            values.append(field_values)
            
        return values


# Example Usage with Different Field Types

def example_app():
    st.title("Streamlit Repeatable Fields Demo")
    
    st.header("Basic Text Input Example")
    
    # Example 1: Simple text inputs
    text_fields = RepeatableField(key_prefix="text_example")
    
    def render_text_field(field_id, index):
        st.text_input(f"Field {index + 1}", key=f"{field_id}_value")
    
    text_fields.render(render_text_field, min_fields=1, max_fields=5)
    
    if st.button("Show Text Values"):
        values = text_fields.get_values("value")
        st.write(values)
    
    st.divider()
    
    # Example 2: Complex form with different field types
    st.header("Complex Form Example")
    
    complex_form = RepeatableField(key_prefix="complex_example")
    
    def render_complex_field(field_id, index):
        with st.expander(f"Person {index + 1}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Name", key=f"{field_id}_name")
                st.number_input("Age", min_value=0, max_value=120, key=f"{field_id}_age")
            
            with col2:
                st.selectbox("Education", 
                             ["High School", "Bachelor's", "Master's", "PhD"], 
                             key=f"{field_id}_education")
                st.checkbox("Employed", key=f"{field_id}_employed")
            
            st.radio("Gender", ["Male", "Female", "Other", "Prefer not to say"], 
                     key=f"{field_id}_gender")
            
            st.slider("Satisfaction", 0, 100, 50, key=f"{field_id}_satisfaction")
    
    complex_form.render(render_complex_field, min_fields=1)
    
    if st.button("Submit Form"):
        values = complex_form.get_values(
            ["name", "age", "education", "employed", "gender", "satisfaction"]
        )
        st.write("Submitted Data:")
        st.json(values)
    
    st.divider()
    
    # Example 3: Custom field builder
    st.header("Build Your Own Form")
    
    st.markdown("### Define Field Types")
    
    field_builder = {}
    col1, col2 = st.columns(2)
    
    with col1:
        field_builder["field_type"] = st.selectbox(
            "Field Type",
            ["Text Input", "Number Input", "Checkbox", "Radio", "Select", "Slider", "Text Area"]
        )
    
    with col2:
        field_builder["field_label"] = st.text_input("Field Label", "My Field")
    
    # Additional options based on field type
    if field_builder["field_type"] in ["Radio", "Select"]:
        options = st.text_input("Options (comma separated)", "Option 1, Option 2, Option 3")
        field_builder["options"] = [opt.strip() for opt in options.split(",")]
    
    if field_builder["field_type"] == "Number Input" or field_builder["field_type"] == "Slider":
        col1, col2 = st.columns(2)
        with col1:
            field_builder["min_value"] = st.number_input("Min Value", value=0)
        with col2:
            field_builder["max_value"] = st.number_input("Max Value", value=100)
    
    # Store the field configuration
    if "custom_fields" not in st.session_state:
        st.session_state.custom_fields = []
    
    if st.button("Add Field to Form"):
        st.session_state.custom_fields.append(field_builder.copy())
    
    # Display all configured fields
    st.markdown("### Current Field Configuration")
    for i, field in enumerate(st.session_state.custom_fields):
        st.write(f"{i+1}. {field['field_label']} ({field['field_type']})")
    
    if st.button("Clear All Fields"):
        st.session_state.custom_fields = []
    
    # Render the custom form if there are fields
    if st.session_state.custom_fields:
        st.markdown("### Your Custom Form")
        
        custom_form = RepeatableField(key_prefix="custom_form")
        
        def render_custom_field(field_id, index):
            st.subheader(f"Entry {index + 1}")
            
            for i, field in enumerate(st.session_state.custom_fields):
                field_key = f"{field_id}_field_{i}"
                
                if field["field_type"] == "Text Input":
                    st.text_input(field["field_label"], key=field_key)
                    
                elif field["field_type"] == "Number Input":
                    st.number_input(field["field_label"], 
                                    min_value=field.get("min_value", 0),
                                    max_value=field.get("max_value", 100),
                                    key=field_key)
                    
                elif field["field_type"] == "Checkbox":
                    st.checkbox(field["field_label"], key=field_key)
                    
                elif field["field_type"] == "Radio":
                    st.radio(field["field_label"], field.get("options", ["Yes", "No"]), key=field_key)
                    
                elif field["field_type"] == "Select":
                    st.selectbox(field["field_label"], field.get("options", ["Option 1"]), key=field_key)
                    
                elif field["field_type"] == "Slider":
                    st.slider(field["field_label"], 
                              min_value=field.get("min_value", 0),
                              max_value=field.get("max_value", 100),
                              key=field_key)
                    
                elif field["field_type"] == "Text Area":
                    st.text_area(field["field_label"], key=field_key)
        
        custom_form.render(render_custom_field)
        
        if st.button("Submit Custom Form"):
            entries = []
            for field_id in st.session_state[f"custom_form_ids"]:
                entry = {}
                for i, field in enumerate(st.session_state.custom_fields):
                    field_key = f"{field_id}_field_{i}"
                    entry[field["field_label"]] = st.session_state.get(field_key)
                entries.append(entry)
            
            st.write("Submitted Custom Form Data:")
            st.json(entries)


# Uncomment to run the example
# if __name__ == "__main__":
#     example_app()
