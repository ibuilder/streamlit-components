import streamlit as st
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import os
from datetime import datetime

def main():
    st.title("Digital Signature Pad")
    
    # CSS for styling the signature pad
    st.markdown("""
    <style>
        .signature-pad {
            border: 2px solid #cccccc;
            border-radius: 5px;
            background-color: #ffffff;
            margin-bottom: 10px;
        }
        .signature-pad canvas {
            width: 100%;
            height: 200px;
        }
        .clear-button {
            margin-top: 10px;
        }
        .signature-tabs {
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .timestamp {
            color: #666666;
            font-size: 12px;
            font-style: italic;
            margin-top: 5px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state variables
    if 'signature' not in st.session_state:
        st.session_state.signature = None
    if 'signature_type' not in st.session_state:
        st.session_state.signature_type = "draw"
    if 'typed_name' not in st.session_state:
        st.session_state.typed_name = ""
    if 'signature_timestamp' not in st.session_state:
        st.session_state.signature_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create tabs for different signature methods
    tab1, tab2 = st.tabs(["Draw Signature", "Type Signature"])
    
    with tab1:
        # Create signature HTML component with JavaScript
        signature_html = """
        <div class="signature-pad">
            <canvas id="signature-pad" width="600" height="200"></canvas>
        </div>
        <button id="clear-button" class="clear-button">Clear Signature</button>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/signature_pad/2.3.2/signature_pad.min.js"></script>
        <script>
            // Initialize the signature pad
            var canvas = document.getElementById("signature-pad");
            var signaturePad = new SignaturePad(canvas);
            
            // Handle window resize
            window.addEventListener("resize", function() {
                var ratio = Math.max(window.devicePixelRatio || 1, 1);
                canvas.width = canvas.offsetWidth * ratio;
                canvas.height = canvas.offsetHeight * ratio;
                canvas.getContext("2d").scale(ratio, ratio);
                signaturePad.clear();
            });
            
            // Clear button functionality
            document.getElementById("clear-button").addEventListener("click", function() {
                signaturePad.clear();
                sendDataToStreamlit("");
            });
            
            // Function to send data to Streamlit
            function sendDataToStreamlit(data) {
                const streamlitDoc = window.parent.document;
                const event = new CustomEvent("streamlit:signature", {detail: {data: data}});
                streamlitDoc.dispatchEvent(event);
            }
            
            // Send signature data when stroke ends
            signaturePad.addEventListener("endStroke", function() {
                if (!signaturePad.isEmpty()) {
                    sendDataToStreamlit(signaturePad.toDataURL());
                }
            });
        </script>
        """
        
        # Custom component to capture signature data
        def capture_signature():
            container = st.empty()
            container.markdown(signature_html, unsafe_allow_html=True)
            
            # Process signature events
            def handle_signature_event(event):
                data = event.detail["data"]
                if data:
                    # Get the base64 string without the data URL prefix
                    encoded_data = data.split(",")[1] if "," in data else ""
                    st.session_state.signature = encoded_data
                    st.session_state.signature_type = "draw"
                    st.session_state.signature_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
            # Register event handler
            st.markdown(
                """
                <script>
                    const streamlitDoc = window.parent.document;
                    streamlitDoc.addEventListener("streamlit:signature", function(event) {
                        window.parent.Streamlit.setComponentValue(event.detail);
                    });
                </script>
                """,
                unsafe_allow_html=True
            )
        
        # Create the signature component
        capture_signature()
    
    with tab2:
        st.write("Type your signature below:")
        
        # Font selection for typed signature
        font_options = ["Cursive", "Handwritten", "Formal", "Simple"]
        selected_font = st.selectbox("Select signature style:", font_options)
        
        # Get the typed name
        typed_name = st.text_input("Full Name:", value=st.session_state.typed_name)
        
        if st.button("Generate Signature"):
            if typed_name.strip():
                st.session_state.typed_name = typed_name
                st.session_state.signature = create_typed_signature(typed_name, selected_font)
                st.session_state.signature_type = "typed"
                st.session_state.signature_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success("Signature generated!")
            else:
                st.warning("Please enter your name first.")
    
    # Actions for handling the signature
    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Signature"):
            if st.session_state.signature:
                save_signature()
                st.success("Signature saved successfully!")
            else:
                st.warning("Please create a signature first.")
    
    with col2:
        if st.button("Download Signature"):
            if st.session_state.signature:
                download_signature()
            else:
                st.warning("Please create a signature first.")
    
    # Display the signature if it exists
    if st.session_state.signature:
        signature_image = get_signature_image()
        if signature_image:
            st.write("---")
            st.subheader("Your Signature")
            st.image(signature_image, width=400)
            st.markdown(f"<div class='timestamp'>Signed on: {st.session_state.signature_timestamp}</div>", unsafe_allow_html=True)

def create_typed_signature(name, font_style):
    """Create an image with typed signature based on selected font style"""
    # Set up image parameters
    width, height = 600, 200
    bg_color = (255, 255, 255)
    text_color = (0, 0, 0)
    
    # Create a blank image
    image = Image.new('RGBA', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Default font (if custom fonts aren't available)
    try:
        # Different font styles (would need to be installed or included with the app)
        if font_style == "Cursive":
            font_path = None  # Would need to include a cursive font
            font_size = 60
            # Fallback to a default font with italic style
            font = ImageFont.truetype("arial.ttf", font_size)
        elif font_style == "Handwritten":
            font_path = None  # Would need to include a handwritten-style font
            font_size = 55
            # Fallback to a default font
            font = ImageFont.truetype("arial.ttf", font_size)
        elif font_style == "Formal":
            font_path = None  # Would need to include a formal font
            font_size = 48
            # Fallback to a default font
            font = ImageFont.truetype("times.ttf" if os.path.exists("/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf") else "arial.ttf", font_size)
        else:  # Simple
            font_path = None
            font_size = 50
            font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        # If font loading fails, use default font
        font = None
        font_size = 50
    
    # Calculate text position to center it
    text_width = draw.textlength(name, font=font) if font else width//2
    text_x = (width - text_width) // 2
    text_y = (height - font_size) // 2
    
    # Draw the text
    draw.text((text_x, text_y), name, fill=text_color, font=font)
    
    # Draw timestamp at bottom
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_font_size = 16
    timestamp_font = ImageFont.truetype("arial.ttf", timestamp_font_size) if font else None
    timestamp_y = height - timestamp_font_size - 10
    draw.text((10, timestamp_y), timestamp, fill=(100, 100, 100), font=timestamp_font)
    
    # Convert to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str

def get_signature_image():
    """Convert base64 signature data to PIL Image"""
    if st.session_state.signature:
        try:
            binary_data = base64.b64decode(st.session_state.signature)
            image = Image.open(io.BytesIO(binary_data))
            return image
        except Exception as e:
            st.error(f"Error processing signature: {e}")
    return None

def save_signature():
    """Save signature to disk"""
    if st.session_state.signature:
        try:
            # Create signatures directory if it doesn't exist
            os.makedirs("signatures", exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sig_type = "typed" if st.session_state.signature_type == "typed" else "drawn"
            filename = f"signatures/signature_{sig_type}_{timestamp}.png"
            
            # Save image
            image = get_signature_image()
            if image:
                # Add timestamp to the image if it's a drawn signature
                if st.session_state.signature_type == "draw":
                    draw = ImageDraw.Draw(image)
                    try:
                        timestamp_font = ImageFont.truetype("arial.ttf", 16)
                    except OSError:
                        timestamp_font = None
                    timestamp_text = f"Signed: {st.session_state.signature_timestamp}"
                    draw.text((10, image.height - 25), timestamp_text, fill=(100, 100, 100), font=timestamp_font)
                
                image.save(filename)
                st.session_state.saved_path = filename
        except Exception as e:
            st.error(f"Error saving signature: {e}")

def download_signature():
    """Allow user to download the signature"""
    if st.session_state.signature:
        try:
            # Get image with timestamp
            image = get_signature_image()
            if image:
                # Add timestamp to the image if it's a drawn signature
                if st.session_state.signature_type == "draw":
                    draw = ImageDraw.Draw(image)
                    try:
                        timestamp_font = ImageFont.truetype("arial.ttf", 16)
                    except OSError:
                        timestamp_font = None
                    timestamp_text = f"Signed: {st.session_state.signature_timestamp}"
                    draw.text((10, image.height - 25), timestamp_text, fill=(100, 100, 100), font=timestamp_font)
                
                # Convert to bytes
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_bytes = buffered.getvalue()
                
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                sig_type = "typed" if st.session_state.signature_type == "typed" else "drawn"
                filename = f"signature_{sig_type}_{timestamp}.png"
                
                # Create download button
                st.download_button(
                    label="Download",
                    data=img_bytes,
                    file_name=filename,
                    mime="image/png"
                )
            else:
                st.error("Error processing signature for download")
        except Exception as e:
            st.error(f"Error downloading signature: {e}")

if __name__ == "__main__":
    main()
