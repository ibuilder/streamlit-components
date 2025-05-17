import streamlit as st
import pandas as pd
from elasticsearch import Elasticsearch
import json
from datetime import datetime
import uuid
import time

# Set page configuration
st.set_page_config(
    page_title="Elasticsearch CRUD Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'elasticsearch_connected' not in st.session_state:
    st.session_state['elasticsearch_connected'] = False
if 'es_client' not in st.session_state:
    st.session_state['es_client'] = None
if 'index_name' not in st.session_state:
    st.session_state['index_name'] = ""
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = None

# Function to connect to Elasticsearch
def connect_to_elasticsearch(host, port, username=None, password=None, use_ssl=False):
    try:
        # Build connection parameters
        connection_params = {
            'hosts': [f"{host}:{port}"]
        }
        
        # Add authentication if provided
        if username and password:
            connection_params['http_auth'] = (username, password)
        
        # Add SSL if enabled
        if use_ssl:
            connection_params['use_ssl'] = True
            connection_params['verify_certs'] = False
            
        # Create Elasticsearch client
        es_client = Elasticsearch(**connection_params)
        
        # Test connection
        if es_client.ping():
            st.session_state['elasticsearch_connected'] = True
            st.session_state['es_client'] = es_client
            return True, "Successfully connected to Elasticsearch!"
        else:
            return False, "Failed to connect to Elasticsearch server. Please check your connection parameters."
    except Exception as e:
        return False, f"Error connecting to Elasticsearch: {str(e)}"

# Function to create index if it doesn't exist
def create_index_if_not_exists(index_name, mappings=None):
    es_client = st.session_state['es_client']
    
    if not es_client.indices.exists(index=index_name):
        # Default mappings if none provided
        if mappings is None:
            mappings = {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "description": {"type": "text"},
                    "category": {"type": "keyword"},
                    "price": {"type": "float"},
                    "quantity": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"}
                }
            }
        
        # Create the index with mappings
        es_client.indices.create(
            index=index_name,
            body={"mappings": mappings}
        )
        return True, f"Index '{index_name}' created successfully!"
    
    return True, f"Index '{index_name}' already exists."

# Function to add a record
def add_record(index_name, record):
    es_client = st.session_state['es_client']
    
    # Add timestamps and ID if not present
    if 'id' not in record:
        record['id'] = str(uuid.uuid4())
    if 'created_at' not in record:
        record['created_at'] = datetime.now().isoformat()
    if 'updated_at' not in record:
        record['updated_at'] = datetime.now().isoformat()
    
    try:
        # Index the document
        response = es_client.index(
            index=index_name,
            id=record['id'],
            body=record,
            refresh=True  # Ensure the document is immediately available for search
        )
        return True, f"Record added successfully with ID: {record['id']}"
    except Exception as e:
        return False, f"Error adding record: {str(e)}"

# Function to search records
def search_records(index_name, query=None, filters=None, sort_by=None, sort_order="asc", size=100):
    es_client = st.session_state['es_client']
    
    # Build the search body
    search_body = {
        "size": size,
        "query": {
            "bool": {
                "must": [],
                "filter": []
            }
        }
    }
    
    # Add query if provided
    if query:
        search_body["query"]["bool"]["must"].append({
            "multi_match": {
                "query": query,
                "fields": ["*"],
                "fuzziness": "AUTO"
            }
        })
    else:
        # If no query is provided, match all documents
        search_body["query"]["bool"]["must"].append({"match_all": {}})
    
    # Add filters if provided
    if filters:
        for field, value in filters.items():
            if value:  # Only add filter if value is not empty
                search_body["query"]["bool"]["filter"].append({
                    "term": {f"{field}.keyword": value}
                })
    
    # Add sorting if provided
    if sort_by:
        search_body["sort"] = [{sort_by: {"order": sort_order}}]
    
    try:
        # Execute the search
        response = es_client.search(
            index=index_name,
            body=search_body
        )
        
        # Extract hits from response
        hits = response['hits']['hits']
        
        # Convert to list of records
        records = [{"_id": hit["_id"], **hit["_source"]} for hit in hits]
        
        return True, records
    except Exception as e:
        return False, f"Error searching records: {str(e)}"

# Function to update a record
def update_record(index_name, record_id, updated_data):
    es_client = st.session_state['es_client']
    
    # Add updated timestamp
    updated_data['updated_at'] = datetime.now().isoformat()
    
    try:
        # Update the document
        response = es_client.update(
            index=index_name,
            id=record_id,
            body={"doc": updated_data},
            refresh=True  # Ensure the update is immediately visible
        )
        return True, f"Record {record_id} updated successfully!"
    except Exception as e:
        return False, f"Error updating record: {str(e)}"

# Function to delete a record
def delete_record(index_name, record_id):
    es_client = st.session_state['es_client']
    
    try:
        # Delete the document
        response = es_client.delete(
            index=index_name,
            id=record_id,
            refresh=True  # Ensure the deletion is immediately visible
        )
        return True, f"Record {record_id} deleted successfully!"
    except Exception as e:
        return False, f"Error deleting record: {str(e)}"

# Function to get index mapping
def get_index_mapping(index_name):
    es_client = st.session_state['es_client']
    
    try:
        mapping = es_client.indices.get_mapping(index=index_name)
        return mapping[index_name]['mappings']['properties']
    except Exception as e:
        st.error(f"Error getting index mapping: {str(e)}")
        return {}

# Sidebar for Elasticsearch connection
with st.sidebar:
    st.title("Elasticsearch Connection")
    
    # Connection parameters
    host = st.text_input("Host", "localhost")
    port = st.text_input("Port", "9200")
    
    # Advanced options in expander
    with st.expander("Advanced Connection Options"):
        use_auth = st.checkbox("Use Authentication")
        if use_auth:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
        else:
            username = None
            password = None
        
        use_ssl = st.checkbox("Use SSL")
    
    # Connect button
    if st.button("Connect to Elasticsearch"):
        success, message = connect_to_elasticsearch(host, port, username, password, use_ssl)
        if success:
            st.success(message)
        else:
            st.error(message)
    
    # Index selection if connected
    if st.session_state['elasticsearch_connected']:
        st.success("Connected to Elasticsearch")
        
        # Index name input
        index_name = st.text_input("Index Name", "products")
        
        # Set index button
        if st.button("Set Index"):
            if index_name:
                success, message = create_index_if_not_exists(index_name)
                if success:
                    st.session_state['index_name'] = index_name
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("Please enter an index name")

# Main content
if not st.session_state['elasticsearch_connected']:
    st.title("Elasticsearch CRUD Dashboard")
    st.info("Please connect to Elasticsearch using the sidebar options")
elif not st.session_state['index_name']:
    st.title("Elasticsearch CRUD Dashboard")
    st.info("Please set an index name in the sidebar")
else:
    st.title(f"Elasticsearch CRUD Dashboard - {st.session_state['index_name']}")
    
    # Create tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs(["View Data", "Add Data", "Update Data", "Delete Data"])
    
    # Get index mapping for field names
    index_mapping = get_index_mapping(st.session_state['index_name'])
    
    # Tab 1: View Data
    with tab1:
        st.header("Search and View Data")
        
        # Search box
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("Search", placeholder="Enter search terms...")
        with col2:
            search_button = st.button("Search")
        
        # Filters and sorting in expandable section
        with st.expander("Advanced Search Options"):
            # Get field names from mapping excluding system fields
            fields = [field for field in index_mapping.keys() 
                    if not field.startswith("_") and field not in ["created_at", "updated_at"]]
            
            # Create filter inputs
            st.subheader("Filters")
            filters = {}
            
            # Create two columns for filters
            filter_cols = st.columns(2)
            
            for i, field in enumerate(fields):
                with filter_cols[i % 2]:
                    filter_value = st.text_input(f"Filter by {field}", key=f"filter_{field}")
                    if filter_value:
                        filters[field] = filter_value
            
            # Sorting options
            st.subheader("Sorting")
            sort_cols = st.columns(2)
            
            with sort_cols[0]:
                sort_by = st.selectbox("Sort by", [""] + fields)
            
            with sort_cols[1]:
                sort_order = st.selectbox("Sort order", ["asc", "desc"])
        
        # Refresh button
        if st.button("Refresh Data", key="refresh_data"):
            search_button = True
        
        # Perform search when button is clicked
        if search_button:
            success, results = search_records(
                st.session_state['index_name'],
                query=search_query,
                filters=filters,
                sort_by=sort_by if sort_by else None,
                sort_order=sort_order
            )
            
            if success:
                st.session_state['search_results'] = results
            else:
                st.error(results)  # Display error message
        
        # Display results if available
        if st.session_state['search_results']:
            results = st.session_state['search_results']
            
            # Convert results to DataFrame for display
            if results:
                df = pd.DataFrame(results)
                
                # Display record count
                st.info(f"Found {len(results)} records")
                
                # Display as an interactive table
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "_id": st.column_config.TextColumn("ID"),
                        "created_at": st.column_config.DatetimeColumn("Created At"),
                        "updated_at": st.column_config.DatetimeColumn("Updated At")
                    }
                )
            else:
                st.info("No records found")
    
    # Tab 2: Add Data
    with tab2:
        st.header("Add New Record")
        
        # Create form for adding data
        with st.form(key="add_record_form"):
            # Get fields from mapping excluding system fields
            fields = [field for field in index_mapping.keys() 
                    if not field.startswith("_") and field not in ["id", "created_at", "updated_at"]]
            
            # Create input fields
            new_record = {}
            
            # Create columns for form fields
            form_cols = st.columns(2)
            
            for i, field in enumerate(fields):
                field_type = index_mapping[field].get("type", "text")
                
                with form_cols[i % 2]:
                    # Create appropriate input based on field type
                    if field_type == "text" or field_type == "keyword":
                        new_record[field] = st.text_input(f"{field.capitalize()}")
                    elif field_type == "integer":
                        new_record[field] = st.number_input(f"{field.capitalize()}", step=1)
                    elif field_type == "float":
                        new_record[field] = st.number_input(f"{field.capitalize()}", step=0.01)
                    elif field_type == "boolean":
                        new_record[field] = st.checkbox(f"{field.capitalize()}")
                    elif field_type == "date":
                        new_record[field] = st.date_input(f"{field.capitalize()}").isoformat()
                    else:
                        new_record[field] = st.text_input(f"{field.capitalize()}")
            
            # Submit button
            submit_button = st.form_submit_button("Add Record")
        
        # Process form submission
        if submit_button:
            # Validate required fields
            if all(new_record.values()):
                success, message = add_record(st.session_state['index_name'], new_record)
                if success:
                    st.success(message)
                    # Clear session state to refresh search results
                    if 'search_results' in st.session_state:
                        st.session_state['search_results'] = None
                    # Add a small delay and then reload the page to show the new record
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please fill in all fields")
    
    # Tab 3: Update Data
    with tab3:
        st.header("Update Existing Record")
        
        # Search for record to update
        record_id = st.text_input("Enter Record ID to Update")
        
        if record_id:
            # Search for the record
            try:
                es_client = st.session_state['es_client']
                record = es_client.get(index=st.session_state['index_name'], id=record_id)
                
                # Display current record values
                st.subheader("Current Record Values")
                st.json(record['_source'])
                
                # Create form for updating data
                with st.form(key="update_record_form"):
                    st.subheader("Update Record Values")
                    
                    # Get fields from mapping excluding system fields
                    fields = [field for field in index_mapping.keys() 
                            if not field.startswith("_") and field not in ["id", "created_at", "updated_at"]]
                    
                    # Create input fields with current values
                    updated_record = {}
                    
                    # Create columns for form fields
                    form_cols = st.columns(2)
                    
                    for i, field in enumerate(fields):
                        field_type = index_mapping[field].get("type", "text")
                        current_value = record['_source'].get(field, "")
                        
                        with form_cols[i % 2]:
                            # Create appropriate input based on field type
                            if field_type == "text" or field_type == "keyword":
                                updated_record[field] = st.text_input(f"{field.capitalize()}", value=current_value)
                            elif field_type == "integer":
                                updated_record[field] = st.number_input(f"{field.capitalize()}", value=float(current_value) if current_value else 0, step=1)
                            elif field_type == "float":
                                updated_record[field] = st.number_input(f"{field.capitalize()}", value=float(current_value) if current_value else 0.0, step=0.01)
                            elif field_type == "boolean":
                                updated_record[field] = st.checkbox(f"{field.capitalize()}", value=bool(current_value))
                            elif field_type == "date":
                                updated_record[field] = st.text_input(f"{field.capitalize()}", value=current_value)
                            else:
                                updated_record[field] = st.text_input(f"{field.capitalize()}", value=current_value)
                    
                    # Submit button
                    update_button = st.form_submit_button("Update Record")
                
                # Process form submission
                if update_button:
                    # Remove empty fields
                    updated_record = {k: v for k, v in updated_record.items() if v != ""}
                    
                    # Update the record
                    if updated_record:
                        success, message = update_record(st.session_state['index_name'], record_id, updated_record)
                        if success:
                            st.success(message)
                            # Clear session state to refresh search results
                            if 'search_results' in st.session_state:
                                st.session_state['search_results'] = None
                            # Add a small delay and then reload the page to show the updated record
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("No changes detected")
            
            except Exception as e:
                st.error(f"Error retrieving record: {str(e)}")
        else:
            st.info("Enter a record ID to update")
    
    # Tab 4: Delete Data
    with tab4:
        st.header("Delete Record")
        
        # Search for record to delete
        record_id = st.text_input("Enter Record ID to Delete")
        
        if record_id:
            # Search for the record
            try:
                es_client = st.session_state['es_client']
                record = es_client.get(index=st.session_state['index_name'], id=record_id)
                
                # Display record to be deleted
                st.subheader("Record to Delete")
                st.json(record['_source'])
                
                # Confirm deletion
                st.warning("Are you sure you want to delete this record? This action cannot be undone.")
                if st.button("Delete Record", key="confirm_delete"):
                    success, message = delete_record(st.session_state['index_name'], record_id)
                    if success:
                        st.success(message)
                        # Clear session state to refresh search results
                        if 'search_results' in st.session_state:
                            st.session_state['search_results'] = None
                        # Add a small delay and then reload the page
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(message)
            
            except Exception as e:
                st.error(f"Error retrieving record: {str(e)}")
        else:
            st.info("Enter a record ID to delete")

# Footer
st.markdown("---")
st.markdown("Elasticsearch CRUD Dashboard | Built with Streamlit")
