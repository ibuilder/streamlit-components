# File: conditional_forms.py
import streamlit as st
from typing import Dict, List, Any, Callable, Optional, Union, Tuple
import uuid
import json
import copy

class Field:
    """Base class for all form fields"""
    
    def __init__(
        self, 
        name: str,
        label: str,
        field_type: str,
        required: bool = False,
        default: Any = None,
        options: List[Any] = None,
        help: str = None,
        validator: Callable[[Any], Tuple[bool, str]] = None,
        **kwargs
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.label = label
        self.field_type = field_type
        self.required = required
        self.default = default
        self.options = options
        self.help = help
        self.validator = validator
        self.value = default
        self.kwargs = kwargs
    
    def render(self, form_state: Dict[str, Any]) -> Any:
        """Render the field and return its value"""
        # Base implementation
        if self.field_type == "text_input":
            self.value = st.text_input(
                label=self.label,
                value=form_state.get(self.name, self.default),
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "text_area":
            self.value = st.text_area(
                label=self.label,
                value=form_state.get(self.name, self.default),
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "number_input":
            self.value = st.number_input(
                label=self.label,
                value=form_state.get(self.name, self.default),
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "checkbox":
            self.value = st.checkbox(
                label=self.label,
                value=form_state.get(self.name, self.default),
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "radio":
            self.value = st.radio(
                label=self.label,
                options=self.options,
                index=self.options.index(form_state.get(self.name, self.default)) if form_state.get(self.name) in self.options else 0,
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "selectbox":
            self.value = st.selectbox(
                label=self.label,
                options=self.options,
                index=self.options.index(form_state.get(self.name, self.default)) if form_state.get(self.name) in self.options else 0,
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "multiselect":
            self.value = st.multiselect(
                label=self.label,
                options=self.options,
                default=form_state.get(self.name, self.default or []),
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "slider":
            self.value = st.slider(
                label=self.label,
                value=form_state.get(self.name, self.default),
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "date_input":
            self.value = st.date_input(
                label=self.label,
                value=form_state.get(self.name, self.default),
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "time_input":
            self.value = st.time_input(
                label=self.label,
                value=form_state.get(self.name, self.default),
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "file_uploader":
            self.value = st.file_uploader(
                label=self.label,
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
        elif self.field_type == "color_picker":
            self.value = st.color_picker(
                label=self.label,
                value=form_state.get(self.name, self.default),
                help=self.help,
                key=f"{self.id}_{self.name}",
                **self.kwargs
            )
            
        return self.value
    
    def validate(self) -> Tuple[bool, str]:
        """Validate the field value"""
        if self.required and (self.value is None or self.value == "" or (isinstance(self.value, list) and len(self.value) == 0)):
            return False, f"{self.label} is required"
        
        if self.validator and self.value is not None:
            return self.validator(self.value)
        
        return True, ""


class FieldSet:
    """A group of fields"""
    
    def __init__(self, name: str, title: str = None, fields: List[Field] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.title = title or name
        self.fields = fields or []
    
    def add_field(self, field: Field) -> 'FieldSet':
        """Add a field to the fieldset"""
        self.fields.append(field)
        return self
    
    def render(self, form_state: Dict[str, Any]) -> Dict[str, Any]:
        """Render all fields in the fieldset"""
        if self.title:
            st.subheader(self.title)
        
        field_values = {}
        for field in self.fields:
            value = field.render(form_state)
            field_values[field.name] = value
            
        return field_values
    
    def validate(self) -> List[Tuple[str, str]]:
        """Validate all fields in the fieldset"""
        errors = []
        for field in self.fields:
            is_valid, error_msg = field.validate()
            if not is_valid:
                errors.append((field.name, error_msg))
        return errors


class Condition:
    """A condition for showing/hiding fields"""
    
    def __init__(
        self, 
        field_name: str, 
        operator: str, 
        value: Any,
        logical_op: str = "and"
    ):
        self.field_name = field_name
        self.operator = operator  # equals, not_equals, contains, not_contains, greater_than, less_than, etc.
        self.value = value
        self.logical_op = logical_op  # and, or
    
    def evaluate(self, form_values: Dict[str, Any]) -> bool:
        """Evaluate the condition against form values"""
        field_value = form_values.get(self.field_name)
        
        if self.operator == "equals":
            return field_value == self.value
        elif self.operator == "not_equals":
            return field_value != self.value
        elif self.operator == "contains":
            if isinstance(field_value, list):
                return self.value in field_value
            elif isinstance(field_value, str):
                return self.value in field_value
            return False
        elif self.operator == "not_contains":
            if isinstance(field_value, list):
                return self.value not in field_value
            elif isinstance(field_value, str):
                return self.value not in field_value
            return True
        elif self.operator == "greater_than":
            return field_value > self.value if field_value is not None else False
        elif self.operator == "less_than":
            return field_value < self.value if field_value is not None else False
        elif self.operator == "in":
            return field_value in self.value if isinstance(self.value, (list, tuple)) else False
        elif self.operator == "not_in":
            return field_value not in self.value if isinstance(self.value, (list, tuple)) else True
        elif self.operator == "is_empty":
            return field_value is None or field_value == "" or (isinstance(field_value, list) and len(field_value) == 0)
        elif self.operator == "is_not_empty":
            return not (field_value is None or field_value == "" or (isinstance(field_value, list) and len(field_value) == 0))
        
        return False


class ConditionalFieldSet(FieldSet):
    """A fieldset that is displayed conditionally"""
    
    def __init__(
        self, 
        name: str, 
        title: str = None, 
        fields: List[Field] = None,
        conditions: List[Condition] = None,
        logical_operator: str = "and"  # "and" or "or"
    ):
        super().__init__(name, title, fields)
        self.conditions = conditions or []
        self.logical_operator = logical_operator
    
    def add_condition(self, condition: Condition) -> 'ConditionalFieldSet':
        """Add a condition to the fieldset"""
        self.conditions.append(condition)
        return self
    
    def should_display(self, form_values: Dict[str, Any]) -> bool:
        """Determine if the fieldset should be displayed based on conditions"""
        if not self.conditions:
            return True
            
        results = [condition.evaluate(form_values) for condition in self.conditions]
        
        if self.logical_operator == "and":
            return all(results)
        else:  # "or"
            return any(results)
    
    def render(self, form_state: Dict[str, Any]) -> Dict[str, Any]:
        """Render the fieldset if conditions are met"""
        if not self.should_display(form_state):
            return {}
            
        return super().render(form_state)


class Form:
    """Main form class that manages fieldsets and form state"""
    
    def __init__(self, name: str, title: str = None, description: str = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.title = title or name
        self.description = description
        self.fieldsets = []
        self.submit_label = "Submit"
        self.reset_label = "Reset"
        self.show_reset = True
        
        # Initialize session state for this form if not exists
        if f"form_{self.id}" not in st.session_state:
            st.session_state[f"form_{self.id}"] = {
                "values": {},
                "submitted": False,
                "validated": False,
                "errors": [],
            }
    
    @property
    def form_state(self) -> Dict[str, Any]:
        """Get the current form state from session state"""
        return st.session_state[f"form_{self.id}"]
    
    @property
    def values(self) -> Dict[str, Any]:
        """Get the current form values"""
        return self.form_state.get("values", {})
    
    @property
    def is_submitted(self) -> bool:
        """Check if the form was submitted"""
        return self.form_state.get("submitted", False)
    
    @property
    def is_valid(self) -> bool:
        """Check if the form is valid"""
        return self.form_state.get("validated", False) and not self.form_state.get("errors", [])
    
    @property
    def errors(self) -> List[Tuple[str, str]]:
        """Get form validation errors"""
        return self.form_state.get("errors", [])
    
    def add_fieldset(self, fieldset: Union[FieldSet, ConditionalFieldSet]) -> 'Form':
        """Add a fieldset to the form"""
        self.fieldsets.append(fieldset)
        return self
    
    def reset(self):
        """Reset the form"""
        st.session_state[f"form_{self.id}"] = {
            "values": {},
            "submitted": False,
            "validated": False,
            "errors": [],
        }
    
    def render(self) -> Dict[str, Any]:
        """Render the form"""
        if self.title:
            st.title(self.title)
        
        if self.description:
            st.markdown(self.description)
        
        form_values = copy.deepcopy(self.values)
        
        # Create a form context with Streamlit
        with st.form(key=f"form_{self.id}"):
            # Render all fieldsets
            for fieldset in self.fieldsets:
                values = fieldset.render(form_values)
                form_values.update(values)
            
            # Form buttons
            col1, col2 = st.columns([1, 4])
            submit_button = col1.form_submit_button(label=self.submit_label)
            
            if self.show_reset:
                reset_button = col2.form_submit_button(label=self.reset_label)
                if reset_button:
                    self.reset()
                    st.rerun()
        
        # Handle form submission
        if submit_button:
            self.form_state["values"] = form_values
            self.form_state["submitted"] = True
            
            # Validate the form
            all_errors = []
            for fieldset in self.fieldsets:
                if isinstance(fieldset, ConditionalFieldSet) and not fieldset.should_display(form_values):
                    continue
                errors = fieldset.validate()
                all_errors.extend(errors)
            
            self.form_state["validated"] = True
            self.form_state["errors"] = all_errors
            
            if all_errors:
                st.error("Please fix the following errors:")
                for field_name, error_msg in all_errors:
                    st.error(f"- {error_msg}")
        
        return form_values


# Helper functions to create fields easily
def text_input(name, label, **kwargs) -> Field:
    return Field(name, label, "text_input", **kwargs)

def text_area(name, label, **kwargs) -> Field:
    return Field(name, label, "text_area", **kwargs)

def number_input(name, label, **kwargs) -> Field:
    return Field(name, label, "number_input", **kwargs)

def checkbox(name, label, **kwargs) -> Field:
    return Field(name, label, "checkbox", **kwargs)

def radio(name, label, options, **kwargs) -> Field:
    return Field(name, label, "radio", options=options, **kwargs)

def selectbox(name, label, options, **kwargs) -> Field:
    return Field(name, label, "selectbox", options=options, **kwargs)

def multiselect(name, label, options, **kwargs) -> Field:
    return Field(name, label, "multiselect", options=options, **kwargs)

def slider(name, label, **kwargs) -> Field:
    return Field(name, label, "slider", **kwargs)

def date_input(name, label, **kwargs) -> Field:
    return Field(name, label, "date_input", **kwargs)

def time_input(name, label, **kwargs) -> Field:
    return Field(name, label, "time_input", **kwargs)

def file_uploader(name, label, **kwargs) -> Field:
    return Field(name, label, "file_uploader", **kwargs)

def color_picker(name, label, **kwargs) -> Field:
    return Field(name, label, "color_picker", **kwargs)

# File: app.py
import streamlit as st
from datetime import date, time, datetime
from conditional_forms import (
    Form, FieldSet, ConditionalFieldSet, Condition,
    text_input, text_area, number_input, checkbox, radio, selectbox,
    multiselect, slider, date_input, time_input, file_uploader, color_picker
)

st.set_page_config(page_title="Advanced Conditional Forms", layout="wide")

def email_validator(value):
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if re.match(pattern, value):
        return True, ""
    else:
        return False, "Please enter a valid email address"

def create_registration_form():
    # Create a form
    form = Form(
        name="registration",
        title="Advanced Registration Form",
        description="Please fill out this form to register. Fields will appear/disappear based on your selections."
    )
    
    # Basic information fieldset
    basic_info = FieldSet(
        name="basic_info",
        title="Basic Information"
    )
    
    basic_info.add_field(text_input("first_name", "First Name", required=True))
    basic_info.add_field(text_input("last_name", "Last Name", required=True))
    basic_info.add_field(text_input("email", "Email Address", required=True, validator=email_validator))
    basic_info.add_field(radio("user_type", "I am a", options=["Individual", "Business", "Non-profit"], required=True))
    
    # Individual details - shown only when user type is Individual
    individual_details = ConditionalFieldSet(
        name="individual_details",
        title="Individual Details",
        conditions=[Condition("user_type", "equals", "Individual")]
    )
    
    individual_details.add_field(date_input("birthdate", "Date of Birth", required=True))
    individual_details.add_field(selectbox("occupation", "Occupation", options=[
        "Student", "Employee", "Self-employed", "Unemployed", "Retired", "Other"
    ]))
    
    # Show additional field only when occupation is Other
    other_occupation = ConditionalFieldSet(
        name="other_occupation",
        conditions=[
            Condition("user_type", "equals", "Individual"),
            Condition("occupation", "equals", "Other")
        ]
    )
    other_occupation.add_field(text_input("occupation_other", "Please specify"))
    
    # Business details - shown only when user type is Business
    business_details = ConditionalFieldSet(
        name="business_details",
        title="Business Details",
        conditions=[Condition("user_type", "equals", "Business")]
    )
    
    business_details.add_field(text_input("company_name", "Company Name", required=True))
    business_details.add_field(number_input("employees", "Number of Employees", min_value=1, value=1))
    business_details.add_field(multiselect("industry", "Industry", options=[
        "Technology", "Finance", "Healthcare", "Education", "Retail", "Manufacturing", "Other"
    ]))
    
    # Non-profit details - shown only when user type is Non-profit
    nonprofit_details = ConditionalFieldSet(
        name="nonprofit_details",
        title="Non-profit Details",
        conditions=[Condition("user_type", "equals", "Non-profit")]
    )
    
    nonprofit_details.add_field(text_input("organization_name", "Organization Name", required=True))
    nonprofit_details.add_field(selectbox("org_type", "Organization Type", options=[
        "Educational", "Religious", "Humanitarian", "Environmental", "Health", "Arts & Culture", "Other"
    ]))
    
    # Contact preferences
    contact_prefs = FieldSet(
        name="contact_prefs",
        title="Contact Preferences"
    )
    
    contact_prefs.add_field(checkbox("subscribe_newsletter", "Subscribe to newsletter", value=True))
    
    # Newsletter preferences - shown only when subscribed to newsletter
    newsletter_prefs = ConditionalFieldSet(
        name="newsletter_prefs",
        title="Newsletter Preferences",
        conditions=[Condition("subscribe_newsletter", "equals", True)]
    )
    
    newsletter_prefs.add_field(multiselect("newsletter_topics", "Topics of Interest", options=[
        "Product Updates", "Industry News", "Tips & Tricks", "Events & Webinars", "Special Offers"
    ]))
    newsletter_prefs.add_field(radio("newsletter_frequency", "Frequency", options=[
        "Daily", "Weekly", "Monthly"
    ], index=1))
    
    # Preferred contact method
    contact_method = FieldSet(
        name="contact_method",
        title="Preferred Contact Method"
    )
    
    contact_method.add_field(selectbox("preferred_contact", "How should we contact you?", options=[
        "Email", "Phone", "Post"
    ]))
    
    # Phone details - shown only when preferred contact is Phone
    phone_details = ConditionalFieldSet(
        name="phone_details",
        conditions=[Condition("preferred_contact", "equals", "Phone")]
    )
    
    phone_details.add_field(text_input("phone_number", "Phone Number", required=True))
    phone_details.add_field(time_input("best_time_to_call", "Best Time to Call", value=time(9, 0)))
    
    # Postal details - shown only when preferred contact is Post
    postal_details = ConditionalFieldSet(
        name="postal_details",
        title="Postal Address",
        conditions=[Condition("preferred_contact", "equals", "Post")]
    )
    
    postal_details.add_field(text_area("address", "Address", required=True))
    postal_details.add_field(text_input("city", "City", required=True))
    postal_details.add_field(text_input("postal_code", "Postal Code", required=True))
    postal_details.add_field(text_input("country", "Country", required=True))
    
    # Additional settings
    additional = FieldSet(
        name="additional",
        title="Additional Settings"
    )
    
    additional.add_field(slider("notification_level", "Notification Level", min_value=0, max_value=10, value=5))
    additional.add_field(color_picker("preferred_color", "Preferred Color Theme", value="#1E88E5"))
    additional.add_field(file_uploader("profile_picture", "Profile Picture (optional)", type=["jpg", "png", "jpeg"]))
    
    # Add all fieldsets to the form
    form.add_fieldset(basic_info)
    form.add_fieldset(individual_details)
    form.add_fieldset(other_occupation)
    form.add_fieldset(business_details)
    form.add_fieldset(nonprofit_details)
    form.add_fieldset(contact_prefs)
    form.add_fieldset(newsletter_prefs)
    form.add_fieldset(contact_method)
    form.add_fieldset(phone_details)
    form.add_fieldset(postal_details)
    form.add_fieldset(additional)
    
    # Render the form
    form_values = form.render()
    
    # Handle form submission
    if form.is_submitted and form.is_valid:
        st.success("Form submitted successfully!")
        st.write("Form values:")
        st.json(form_values)

if __name__ == "__main__":
    create_registration_form()

# File: advanced_example.py
import streamlit as st
from datetime import date, time, datetime
from conditional_forms import (
    Form, FieldSet, ConditionalFieldSet, Condition,
    text_input, text_area, number_input, checkbox, radio, selectbox,
    multiselect, slider, date_input, time_input, file_uploader, color_picker
)

st.set_page_config(page_title="Complex Conditional Form Demo", layout="wide")

def create_dynamic_survey():
    # Create a form
    form = Form(
        name="dynamic_survey",
        title="Dynamic Multi-stage Survey",
        description="This survey adapts to your responses with complex conditional logic."
    )
    
    # Initial section - Survey type selection
    survey_type = FieldSet(
        name="survey_type",
        title="Survey Type"
    )
    
    survey_type.add_field(radio(
        "survey_category", 
        "Please select a survey category:",
        options=["Product Feedback", "User Experience", "Market Research", "Employee Satisfaction"],
        required=True
    ))
    
    # Product Feedback path
    product_feedback = ConditionalFieldSet(
        name="product_feedback",
        title="Product Feedback",
        conditions=[Condition("survey_category", "equals", "Product Feedback")]
    )
    
    product_feedback.add_field(multiselect(
        "products_used",
        "Which of our products have you used? (Select all that apply)",
        options=["Product A", "Product B", "Product C", "Product D"],
        required=True
    ))
    
    # Product A specific questions
    product_a_questions = ConditionalFieldSet(
        name="product_a_questions",
        title="About Product A",
        conditions=[
            Condition("survey_category", "equals", "Product Feedback"),
            Condition("products_used", "contains", "Product A")
        ]
    )
    
    product_a_questions.add_field(slider(
        "product_a_rating",
        "How would you rate Product A?",
        min_value=1, max_value=10, value=5
    ))
    product_a_questions.add_field(checkbox("product_a_recommend", "Would you recommend Product A to others?"))
    
    # Product A recommendation follow-up
    product_a_recommend_reason = ConditionalFieldSet(
        name="product_a_recommend_reason",
        conditions=[
            Condition("survey_category", "equals", "Product Feedback"),
            Condition("products_used", "contains", "Product A"),
            Condition("product_a_recommend", "equals", True)
        ]
    )
    
    product_a_recommend_reason.add_field(text_area(
        "product_a_recommend_why",
        "Great! What do you like most about Product A?"
    ))
    
    # Product A non-recommendation follow-up
    product_a_non_recommend_reason = ConditionalFieldSet(
        name="product_a_non_recommend_reason",
        conditions=[
            Condition("survey_category", "equals", "Product Feedback"),
            Condition("products_used", "contains", "Product A"),
            Condition("product_a_recommend", "equals", False)
        ]
    )
    
    product_a_non_recommend_reason.add_field(multiselect(
        "product_a_improvement",
        "What aspects of Product A need improvement?",
        options=["Usability", "Performance", "Features", "Reliability", "Price", "Support"]
    ))
    
    # Similarly for Product B, C, D (simplified for brevity)
    product_b_questions = ConditionalFieldSet(
        name="product_b_questions",
        title="About Product B",
        conditions=[
            Condition("survey_category", "equals", "Product Feedback"),
            Condition("products_used", "contains", "Product B")
        ]
    )
    
    product_b_questions.add_field(slider(
        "product_b_rating",
        "How would you rate Product B?",
        min_value=1, max_value=10, value=5
    ))
    
    # User Experience path
    user_experience = ConditionalFieldSet(
        name="user_experience",
        title="User Experience Survey",
        conditions=[Condition("survey_category", "equals", "User Experience")]
    )
    
    user_experience.add_field(selectbox(
        "usage_frequency",
        "How frequently do you use our platform?",
        options=["Daily", "Weekly", "Monthly", "Rarely", "First-time user"]
    ))
    
    # Follow-up based on usage frequency
    frequent_user = ConditionalFieldSet(
        name="frequent_user",
        title="Frequent User Experience",
        conditions=[
            Condition("survey_category", "equals", "User Experience"),
            Condition("usage_frequency", "in", ["Daily", "Weekly"])
        ]
    )
    
    frequent_user.add_field(multiselect(
        "frequent_features",
        "Which features do you use most often?",
        options=["Feature 1", "Feature 2", "Feature 3", "Feature 4", "Feature 5"]
    ))
    
    # Advanced customization options for frequent users
    power_user_options = ConditionalFieldSet(
        name="power_user_options",
        title="Advanced Customization Options",
        conditions=[
            Condition("survey_category", "equals", "User Experience"),
            Condition("usage_frequency", "equals", "Daily"),
            Condition("frequent_features", "contains", "Feature 3")
        ]
    )
    
    power_user_options.add_field(checkbox("advanced_mode", "Do you use advanced mode?"))
    power_user_options.add_field(checkbox("custom_shortcuts", "Have you created custom shortcuts?"))
    
    # Infrequent user
    infrequent_user = ConditionalFieldSet(
        name="infrequent_user",
        title="Infrequent User Experience",
        conditions=[
            Condition("survey_category", "equals", "User Experience"),
            Condition("usage_frequency", "in", ["Monthly", "Rarely", "First-time user"])
        ]
    )
    
    infrequent_user.add_field(radio(
        "usage_difficulty",
        "How difficult is it to use our platform when you return to it?",
        options=["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"]
    ))
    
    # Difficult experience follow-up
    difficulty_followup = ConditionalFieldSet(
        name="difficulty_followup",
        conditions=[
            Condition("survey_category", "equals", "User Experience"),
            Condition("usage_frequency", "in", ["Monthly", "Rarely", "First-time user"]),
            Condition("usage_difficulty", "in", ["Difficult", "Very difficult"])
        ]
    )
    
    difficulty_followup.add_field(text_area(
        "difficulty_explanation",
        "Please explain what makes it difficult to use:"
    ))
    
    # Market Research path
    market_research = ConditionalFieldSet(
        name="market_research",
        title="Market Research",
        conditions=[Condition("survey_category", "equals", "Market Research")]
    )
    
    market_research.add_field(selectbox(
        "industry",
        "Which industry are you in?",
        options=[
            "Technology", "Healthcare", "Finance", "Education", 
            "Manufacturing", "Retail", "Other"
        ]
    ))
    
    # Industry-specific questions
    tech_industry = ConditionalFieldSet(
        name="tech_industry",
        title="Technology Industry Questions",
        conditions=[
            Condition("survey_category", "equals", "Market Research"),
            Condition("industry", "equals", "Technology")
        ]
    )
    
    tech_industry.add_field(multiselect(
        "tech_focus",
        "What technology areas does your company focus on?",
        options=["AI", "Cloud", "IoT", "Mobile", "Security", "Other"]
    ))
    
    # AI focus follow-up
    ai_focus = ConditionalFieldSet(
        name="ai_focus",
        title="AI Focus",
        conditions=[
            Condition("survey_category", "equals", "Market Research"),
            Condition("industry", "equals", "Technology"),
            Condition("tech_focus", "contains", "AI")
        ]
    )
    
    ai_focus.add_field(multiselect(
        "ai_applications",
        "What AI applications are you most interested in?",
        options=["Machine Learning", "Natural Language Processing", "Computer Vision", "Robotics", "Other"]
    ))
    
    # Employee Satisfaction path
    employee_satisfaction = ConditionalFieldSet(
        name="employee_satisfaction",
        title="Employee Satisfaction",
        conditions=[Condition("survey_category", "equals", "Employee Satisfaction")]
    )
    
    employee_satisfaction.add_field(radio(
        "employment_status",
        "What is your employment status?",
        options=["Full-time", "Part-time", "Contract", "Remote"]
    ))
    
    employee_satisfaction.add_field(slider(
        "work_satisfaction",
        "How satisfied are you with your work environment?",
        min_value=1, max_value=10, value=5
    ))
    
    # Low satisfaction follow-up
    low_satisfaction = ConditionalFieldSet(
        name="low_satisfaction",
        title="Areas for Improvement",
        conditions=[
            Condition("survey_category", "equals", "Employee Satisfaction"),
            Condition("work_satisfaction", "less_than", 5)
        ]
    )
    
    low_satisfaction.add_field(multiselect(
        "improvement_areas",
        "Which areas need the most improvement?",
        options=["Work-life balance", "Compensation", "Management", "Tools & Resources", "Office environment", "Other"]
    ))
    
    # Final common section
    final_section = FieldSet(
        name="final_section",
        title="Final Feedback"
    )
    
    final_section.add_field(text_area("additional_comments", "Any additional comments or suggestions?"))
    final_section.add_field(checkbox("contact_for_followup", "May we contact you for follow-up questions?"))
    
    # Contact information - only if follow-up is allowed
    contact_info = ConditionalFieldSet(
        name="contact_info",
        title="Contact Information",
        conditions=[Condition("contact_for_followup", "equals", True)]
    )
    
    contact_info.add_field(text_input("contact_name", "Your Name", required=True))
    contact_info.add_field(text_input("contact_email", "Your Email", required=True))
    
    # Add all fieldsets to the form
    form.add_fieldset(survey_type)
    form.add_fieldset(product_feedback)
    form.add_fieldset(product_a_questions)
    form.add_fieldset(product_a_recommend_reason)
    form.add_fieldset(product_a_non_recommend_reason)
    form.add_fieldset(product_b_questions)
    form.add_fieldset(user_experience)
    form.add_fieldset(frequent_user)
    form.add_fieldset(power_user_options)
    form.add_fieldset(infrequent_user)
    form.add_fieldset(difficulty_followup)
    form.add_fieldset(market_research)
    form.add_fieldset(tech_industry)
    form.add_fieldset(ai_focus)
    form.add_fieldset(employee_satisfaction)
    form.add_fieldset(low_satisfaction)
    form.add_fieldset(final_section)
    form.add_fieldset(contact_info)
    
    # Render the form
    form_values = form.render()
    
    # Handle form submission
    if form.is_submitted and form.is_valid:
        st.success("Survey submitted successfully! Thank you for your feedback.")
        
        # In a real application, you'd save this data to a database
        st.write("Survey results:")
        st.json(form_values)

if __name__ == "__main__":
    create_dynamic_survey()

# File: README.md
# Streamlit Conditional Forms

A powerful library for creating dynamic, conditional forms in Streamlit applications.

## Features

- Support for all Streamlit form field types
- Conditional fieldsets that show/hide based on other field values
- Complex logic with multiple conditions and AND/OR operators
- Form validation with built-in and custom validators
- Persistent form state through Streamlit's session state
- Easy API for creating and configuring forms

## Installation

1. Download the files in this repository
2. Place `conditional_forms.py` in your project directory

## Basic Usage

```python
import streamlit as st
from conditional_forms import Form, FieldSet, text_input

# Create a simple form
form = Form(name="simple_form", title="Simple Form")

# Create a fieldset for basic info
basic_info = FieldSet(name="basic_info", title="Basic Information")
basic_info.add_field(text_input("name", "Your Name", required=True))
basic_info.add_field(text_input("email", "Email Address", required=True))

# Add the fieldset to the form
form.add_fieldset(basic_info)

# Render the form
form_values = form.render()

# Handle submission
if form.is_submitted and form.is_valid:
    st.success("Form submitted successfully!")
    st.write(form_values)
```

## Advanced Usage

See `app.py` for a registration form example with conditional logic.
See `advanced_example.py` for a complex multi-stage survey with nested conditions.

## Documentation

### Field Types

The library supports all Streamlit field types:
- `text_input`: Text input field
- `text_area`: Multi-line text input
- `number_input`: Numeric input field
- `checkbox`: Boolean checkbox
- `radio`: Radio button group
- `selectbox`: Dropdown selection
- `multiselect`: Multiple selection dropdown
- `slider`: Numeric slider
- `date_input`: Date picker
- `time_input`: Time picker
- `file_uploader`: File upload field
- `color_picker`: Color selection field

### Conditional Logic

Conditions can be created with various operators:
- `equals`: Field value equals a specific value
- `not_equals`: Field value is not equal to a specific value
- `contains`: Field value contains a specific value (for lists and strings)
- `not_contains`: Field value doesn't contain a specific value
- `greater_than`: Field value is greater than a specific value
- `less_than`: Field value is less than a specific value
- `in`: Field value is in a list of values
- `not_in`: Field value is not in a list of values
- `is_empty`: Field value is empty
- `is_not_empty`: Field value is not empty

Multiple conditions can be combined with logical operators (AND/OR).

## License

This project is released under the MIT License.
