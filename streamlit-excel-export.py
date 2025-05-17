import streamlit as st
import pandas as pd
import base64
from io import BytesIO
from typing import Union, Optional, List, Dict, Any


def to_excel_download_button(
    df: pd.DataFrame,
    filename: str = "data.xlsx",
    button_text: str = "Download Excel file",
    button_key: Optional[str] = None,
    use_container_width: bool = False,
    sheet_name: str = "Sheet1",
    include_index: bool = False,
    include_header: bool = True,
    additional_sheets: Optional[Dict[str, pd.DataFrame]] = None,
    excel_kwargs: Optional[Dict[str, Any]] = None
) -> None:
    """
    Creates a download button that allows users to download a DataFrame as an Excel file.
    
    Parameters:
    -----------
    df : pd.DataFrame
        The DataFrame to export as Excel
    filename : str
        The name of the file to be downloaded
    button_text : str
        The text to display on the button
    button_key : Optional[str]
        A unique key for the button (needed when using multiple buttons)
    use_container_width : bool
        Whether to stretch the button to the container width
    sheet_name : str
        The name of the sheet in the Excel file
    include_index : bool
        Whether to include the index in the Excel file
    include_header : bool
        Whether to include the column headers in the Excel file
    additional_sheets : Optional[Dict[str, pd.DataFrame]]
        A dictionary mapping sheet names to DataFrames for multi-sheet Excel files
    excel_kwargs : Optional[Dict[str, Any]]
        Additional keyword arguments to pass to DataFrame.to_excel()
    
    Returns:
    --------
    None
        The function generates a streamlit button for downloading the Excel file
    """
    # Ensure excel_kwargs is not None
    if excel_kwargs is None:
        excel_kwargs = {}
    
    # Create a BytesIO buffer
    output = BytesIO()
    
    # Create an Excel writer
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write the main DataFrame to Excel
        df.to_excel(
            writer, 
            sheet_name=sheet_name,
            index=include_index,
            header=include_header,
            **excel_kwargs
        )
        
        # Write additional sheets if provided
        if additional_sheets:
            for sheet, data in additional_sheets.items():
                data.to_excel(
                    writer, 
                    sheet_name=sheet,
                    index=include_index,
                    header=include_header,
                    **excel_kwargs
                )
        
        # The writer has to be saved and closed to apply formatting
        writer.save()
    
    # Get the binary data
    processed_data = output.getvalue()
    
    # Create a base64 encoded string
    b64 = base64.b64encode(processed_data).decode()
    
    # Create the download button
    download_button_str = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{button_text}</a>'
    
    # Display the button
    button_uuid = button_key or f"excel_download_{filename}"
    st.download_button(
        label=button_text,
        data=processed_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=button_uuid,
        use_container_width=use_container_width
    )


# Example usage
def example():
    st.title("Streamlit Excel Export Example")
    
    # Create sample data
    data = {
        'Name': ['John', 'Anna', 'Peter', 'Linda'],
        'Age': [28, 34, 42, 37],
        'City': ['New York', 'Paris', 'Berlin', 'London'],
        'Salary': [65000, 72000, 83000, 91000]
    }
    
    df = pd.DataFrame(data)
    
    # Display the DataFrame
    st.write("### Sample Data")
    st.dataframe(df)
    
    # Basic usage
    st.write("### Basic Excel Export")
    to_excel_download_button(
        df=df,
        filename="employee_data.xlsx",
        button_text="Download Employee Data"
    )
    
    # Multi-sheet example
    st.write("### Multi-Sheet Excel Export")
    
    # Create a second DataFrame for demonstration
    sales_data = {
        'Product': ['Widget A', 'Widget B', 'Widget C', 'Widget D'],
        'Q1': [12500, 15700, 9800, 7400],
        'Q2': [14200, 16300, 11200, 8100],
        'Q3': [13800, 17500, 10900, 9200],
        'Q4': [16700, 18900, 14500, 10800]
    }
    sales_df = pd.DataFrame(sales_data)
    
    # Create a dictionary of additional sheets
    additional_sheets = {
        "Sales Data": sales_df
    }
    
    # Create a multi-sheet Excel download button
    to_excel_download_button(
        df=df,
        filename="company_data.xlsx",
        button_text="Download Company Data (Multi-Sheet)",
        button_key="multi_sheet_download",
        sheet_name="Employee Data",
        additional_sheets=additional_sheets,
        use_container_width=True
    )
    
    # Advanced formatting example
    st.write("### Advanced Excel Export")
    st.write("This example includes additional formatting options.")
    
    # Create a more complex button with additional options
    to_excel_download_button(
        df=df,
        filename="formatted_data.xlsx",
        button_text="Download Formatted Data",
        button_key="formatted_download",
        include_index=True,
        excel_kwargs={
            "startrow": 1,  # Start writing data from row 1 (0-indexed)
            "freeze_panes": (2, 0),  # Freeze the first row
        }
    )


# Uncomment to run the example
# if __name__ == "__main__":
#     example()
