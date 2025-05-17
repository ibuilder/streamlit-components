"""
Streamlit component for viewing IFC models using IFC.js

This package contains a Streamlit component that wraps IFC.js to provide
3D BIM visualization with walkthrough navigation, element selection,
and measurement capabilities.
"""

import os
import streamlit as st
import streamlit.components.v1 as components
import base64

# Define the IFC.js component
_RELEASE = True  # Set to False for development

if not _RELEASE:
    _component_func = components.declare_component(
        "ifcjs_viewer",
        url="http://localhost:3001",  # Local development server URL
    )
else:
    # When released, the component is served from the streamlit server
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("ifcjs_viewer", path=build_dir)


def ifcjs_viewer(ifc_file=None, height=600, key=None):
    """
    Create an IFC.js viewer component.
    
    Parameters:
    -----------
    ifc_file : str or bytes
        Path to IFC file or IFC file content as bytes
    height : int
        Height of the viewer in pixels
    key : str
        Unique key for the component instance
        
    Returns:
    --------
    dict
        Information about selected elements or measurements
    """
    if ifc_file is not None:
        if isinstance(ifc_file, str) and os.path.exists(ifc_file):
            with open(ifc_file, "rb") as f:
                ifc_bytes = f.read()
            ifc_base64 = base64.b64encode(ifc_bytes).decode("utf-8")
        elif isinstance(ifc_file, bytes):
            ifc_base64 = base64.b64encode(ifc_file).decode("utf-8")
        else:
            raise ValueError("ifc_file must be a valid file path or bytes")
    else:
        ifc_base64 = None
        
    component_value = _component_func(ifcData=ifc_base64, height=height, key=key, default=None)
    return component_value


# Frontend code (to be placed in a separate file in your actual implementation)
# This is the HTML/JavaScript code that will be rendered in the Streamlit app
_FRONTEND_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IFC.js Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r132/three.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/web-ifc/0.0.35/web-ifc-api.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/web-ifc-three/0.0.115/web-ifc-three.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/web-ifc-viewer/1.0.207/components.min.js"></script>
    <style>
        body, html {
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
        }
        
        #viewer-container {
            width: 100%;
            height: 100%;
            position: relative;
        }
        
        .toolbar {
            position: absolute;
            top: 10px;
            left: 10px;
            z-index: 1;
            background-color: rgba(255, 255, 255, 0.7);
            padding: 10px;
            border-radius: 5px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .toolbar button {
            padding: 5px 10px;
            cursor: pointer;
        }
        
        .info-panel {
            position: absolute;
            bottom: 10px;
            right: 10px;
            background-color: rgba(255, 255, 255, 0.7);
            padding: 10px;
            border-radius: 5px;
            max-width: 300px;
            max-height: 200px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div id="viewer-container">
        <div class="toolbar">
            <button id="walk-mode-btn">Walk Mode</button>
            <button id="select-mode-btn">Select Mode</button>
            <button id="measure-mode-btn">Measure</button>
            <button id="reset-view-btn">Reset View</button>
        </div>
        <div id="info-panel" class="info-panel" style="display: none;"></div>
    </div>

    <script>
        // Initialize IFC.js viewer
        const container = document.getElementById('viewer-container');
        const viewer = new WebIFCViewer.IfcViewerAPI({
            container,
            backgroundColor: new THREE.Color(0xffffff),
        });
        
        // Set up camera controls
        viewer.context.ifcCamera.cameraControls.enableDamping = true;
        viewer.context.ifcCamera.cameraControls.dampingFactor = 0.2;
        viewer.context.ifcCamera.cameraControls.minDistance = 0.1;
        viewer.context.ifcCamera.cameraControls.maxDistance = 1000;
        
        // Create grid and axes
        viewer.grid.setGrid();
        viewer.axes.setAxes();
        
        // Add UI event listeners
        document.getElementById('walk-mode-btn').addEventListener('click', enableWalkMode);
        document.getElementById('select-mode-btn').addEventListener('click', enableSelectMode);
        document.getElementById('measure-mode-btn').addEventListener('click', enableMeasureMode);
        document.getElementById('reset-view-btn').addEventListener('click', resetView);
        
        // Modes
        let currentMode = 'orbit';
        let walkSpeed = 0.5;
        let walkControls = null;
        
        // Element selection
        let selectedElement = null;
        let preselectedElement = null;
        const infoPanel = document.getElementById('info-panel');
        
        // Measurement
        let measurementPoints = [];
        let measurementLines = null;
        
        function enableWalkMode() {
            if (currentMode === 'walk') return;
            
            currentMode = 'walk';
            resetModes();
            
            // Setup first person controls
            const cameraControls = viewer.context.ifcCamera.cameraControls;
            
            // Store original position to restore it later
            const originalTarget = cameraControls.target.clone();
            const originalPosition = viewer.context.ifcCamera.camera.position.clone();
            
            // Set up walk navigation
            cameraControls.setPosition(originalPosition.x, originalPosition.y + 1.7, originalPosition.z);
            cameraControls.setTarget(
                originalPosition.x + Math.sin(viewer.context.ifcCamera.camera.rotation.y),
                originalPosition.y + 1.7,
                originalPosition.z + Math.cos(viewer.context.ifcCamera.camera.rotation.y)
            );
            
            // Set up keyboard controls for walking
            const keyStates = {};
            
            document.addEventListener('keydown', (event) => {
                if (currentMode !== 'walk') return;
                keyStates[event.code] = true;
            });
            
            document.addEventListener('keyup', (event) => {
                if (currentMode !== 'walk') return;
                keyStates[event.code] = false;
            });
            
            walkControls = setInterval(() => {
                if (currentMode !== 'walk') return;
                
                const camera = viewer.context.ifcCamera.camera;
                const direction = new THREE.Vector3();
                const speed = walkSpeed;
                
                camera.getWorldDirection(direction);
                direction.y = 0;
                direction.normalize();
                
                if (keyStates['KeyW']) {
                    camera.position.addScaledVector(direction, speed);
                    cameraControls.setTarget(
                        camera.position.x + direction.x,
                        camera.position.y,
                        camera.position.z + direction.z
                    );
                }
                
                if (keyStates['KeyS']) {
                    camera.position.addScaledVector(direction, -speed);
                    cameraControls.setTarget(
                        camera.position.x - direction.x,
                        camera.position.y,
                        camera.position.z - direction.z
                    );
                }
                
                const right = new THREE.Vector3().crossVectors(direction, new THREE.Vector3(0, 1, 0));
                
                if (keyStates['KeyA']) {
                    camera.position.addScaledVector(right, -speed);
                    cameraControls.setTarget(
                        camera.position.x + direction.x,
                        camera.position.y,
                        camera.position.z + direction.z
                    );
                }
                
                if (keyStates['KeyD']) {
                    camera.position.addScaledVector(right, speed);
                    cameraControls.setTarget(
                        camera.position.x + direction.x,
                        camera.position.y,
                        camera.position.z + direction.z
                    );
                }
                
                // Up and down
                if (keyStates['KeyE']) {
                    camera.position.y += speed;
                    cameraControls.setTarget(
                        camera.position.x + direction.x,
                        camera.position.y,
                        camera.position.z + direction.z
                    );
                }
                
                if (keyStates['KeyQ']) {
                    camera.position.y -= speed;
                    cameraControls.setTarget(
                        camera.position.x + direction.x,
                        camera.position.y,
                        camera.position.z + direction.z
                    );
                }
                
                cameraControls.update();
            }, 16);
            
            // Update UI to show active mode
            updateButtonStyles('walk-mode-btn');
        }
        
        function enableSelectMode() {
            if (currentMode === 'select') return;
            
            currentMode = 'select';
            resetModes();
            
            // Setup selection
            window.onmousemove = async (event) => {
                if (currentMode !== 'select') return;
                
                const result = await viewer.IFC.selector.castRayIfc(event);
                
                if (result && result.modelID !== undefined && result.id !== undefined) {
                    // Preselect element
                    if (preselectedElement) {
                        viewer.IFC.selector.unHighlight(preselectedElement.modelID, preselectedElement.id);
                    }
                    
                    preselectedElement = { modelID: result.modelID, id: result.id };
                    viewer.IFC.selector.preHighlight(result.modelID, result.id);
                } else if (preselectedElement) {
                    // Unhighlight if no element under cursor
                    viewer.IFC.selector.unHighlight(preselectedElement.modelID, preselectedElement.id);
                    preselectedElement = null;
                }
            };
            
            window.onclick = async (event) => {
                if (currentMode !== 'select' || !preselectedElement) return;
                
                // Unhighlight previous selection
                if (selectedElement) {
                    viewer.IFC.selector.unHighlight(selectedElement.modelID, selectedElement.id);
                }
                
                // Highlight new selection
                selectedElement = { ...preselectedElement };
                viewer.IFC.selector.highlight(selectedElement.modelID, selectedElement.id);
                
                // Get element properties
                const props = await viewer.IFC.getProperties(selectedElement.modelID, selectedElement.id, true);
                displayElementInfo(props);
                
                // Communicate with Streamlit
                const componentValue = {
                    type: 'selection',
                    globalId: props.GlobalId?.value || 'Unknown',
                    type: props.Name?.value || props.type || 'Unknown',
                    properties: props
                };
                
                // Send data to Streamlit
                if (window.Streamlit) {
                    window.Streamlit.setComponentValue(componentValue);
                }
            };
            
            // Update UI to show active mode
            updateButtonStyles('select-mode-btn');
        }
        
        function enableMeasureMode() {
            if (currentMode === 'measure') return;
            
            currentMode = 'measure';
            resetModes();
            
            // Create measurement tool
            viewer.dimensions.active = true;
            viewer.dimensions.previewActive = true;
            
            // Click handler for measurement
            window.onclick = async (event) => {
                if (currentMode !== 'measure') return;
                
                const result = await viewer.IFC.selector.castRayIfc(event);
                
                if (!result) return;
                
                // Create a measurement point
                const point = result.point;
                measurementPoints.push(point);
                
                // If we have 2 points, create a measurement
                if (measurementPoints.length === 2) {
                    const distance = point.distanceTo(measurementPoints[0]);
                    
                    // Create visual line
                    viewer.dimensions.create(measurementPoints[0], measurementPoints[1]);
                    
                    // Reset for next measurement
                    measurementPoints = [];
                    
                    // Communicate with Streamlit
                    const componentValue = {
                        type: 'measurement',
                        point1: [measurementPoints[0].x, measurementPoints[0].y, measurementPoints[0].z],
                        point2: [measurementPoints[1].x, measurementPoints[1].y, measurementPoints[1].z],
                        distance: distance
                    };
                    
                    // Send data to Streamlit
                    if (window.Streamlit) {
                        window.Streamlit.setComponentValue(componentValue);
                    }
                }
            };
            
            // Update UI to show active mode
            updateButtonStyles('measure-mode-btn');
        }
        
        function resetView() {
            // Reset camera to default position
            viewer.context.ifcCamera.cameraControls.setPosition(10, 10, 10);
            viewer.context.ifcCamera.cameraControls.setTarget(0, 0, 0);
        }
        
        function resetModes() {
            // Clear previous mode settings
            if (walkControls) {
                clearInterval(walkControls);
                walkControls = null;
            }
            
            // Reset selector
            window.onmousemove = null;
            window.onclick = null;
            
            if (preselectedElement) {
                viewer.IFC.selector.unHighlight(preselectedElement.modelID, preselectedElement.id);
                preselectedElement = null;
            }
            
            // Reset measurement
            viewer.dimensions.active = false;
            viewer.dimensions.previewActive = false;
            measurementPoints = [];
        }
        
        function updateButtonStyles(activeButtonId) {
            // Reset all buttons
            document.querySelectorAll('.toolbar button').forEach(btn => {
                btn.style.backgroundColor = '';
                btn.style.fontWeight = 'normal';
            });
            
            // Highlight active button
            document.getElementById(activeButtonId).style.backgroundColor = '#4CAF50';
            document.getElementById(activeButtonId).style.fontWeight = 'bold';
        }
        
        function displayElementInfo(props) {
            // Format and display element information
            infoPanel.style.display = 'block';
            
            let html = '<h3>Element Information</h3>';
            
            if (props.GlobalId) {
                html += `<p><strong>ID:</strong> ${props.GlobalId.value}</p>`;
            }
            
            if (props.Name) {
                html += `<p><strong>Name:</strong> ${props.Name.value}</p>`;
            }
            
            if (props.type) {
                html += `<p><strong>Type:</strong> ${props.type}</p>`;
            }
            
            if (props.ObjectType) {
                html += `<p><strong>Object Type:</strong> ${props.ObjectType.value}</p>`;
            }
            
            infoPanel.innerHTML = html;
        }
        
        // Streamlit component initialization
        function initialize() {
            // First, check if we're in a Streamlit app
            if (window.Streamlit) {
                // Initialize and receive data from Streamlit
                function onRender(event) {
                    const data = event.detail.args.ifcData;
                    const height = event.detail.args.height || 600;
                    
                    // Set container height
                    container.style.height = `${height}px`;
                    
                    // If we have IFC data, load it
                    if (data) {
                        loadIFCModel(data);
                    }
                    
                    // Let Streamlit know the component is ready
                    window.Streamlit.setFrameHeight(height);
                    window.Streamlit.setComponentReady();
                }
                
                window.Streamlit.events.addEventListener(window.Streamlit.RENDER_EVENT, onRender);
                window.Streamlit.setComponentReady();
            } else {
                // If not in Streamlit, just set a default height
                container.style.height = '600px';
            }
        }
        
        async function loadIFCModel(base64Data) {
            try {
                // Convert base64 data to binary
                const binaryString = window.atob(base64Data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                
                // Load the IFC model
                const modelID = await viewer.IFC.loadIfc(bytes.buffer, true);
                
                // Center and fit the model in view
                viewer.context.ifcCamera.cameraControls.fitToSphere(
                    viewer.context.getIfcRootScene(modelID).children[0], 
                    true
                );
                
                // Setup spatial tree for fast picking
                await viewer.IFC.selector.prepickIfcModel(modelID);
                
                console.log('IFC model loaded successfully!');
                return modelID;
            } catch (error) {
                console.error('Error loading IFC model:', error);
                return null;
            }
        }
        
        // Initialize the component
        initialize();
    </script>
</body>
</html>
"""

# Function to create the frontend directory and files
def save_frontend(directory="frontend"):
    """
    Save the frontend HTML to a file.
    This is a helper function for development and packaging.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    frontend_path = os.path.join(directory, "index.html")
    with open(frontend_path, "w") as f:
        f.write(_FRONTEND_HTML)
    
    print(f"Frontend saved to {frontend_path}")


# Example usage
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    
    st.title("IFC.js Viewer in Streamlit")
    
    st.markdown("""
    ## IFC Model Viewer with Walk-through, Selection, and Measurement
    
    This component allows you to:
    - Navigate through 3D BIM models (use WASD keys in Walk Mode)
    - Select building elements to view their properties
    - Measure distances between points
    
    Upload an IFC file to get started.
    """)
    
    uploaded_file = st.file_uploader("Upload IFC file", type=["ifc"])
    
    if uploaded_file is not None:
        ifc_bytes = uploaded_file.getvalue()
        
        col1, col2 = st.columns([7, 3])
        
        with col1:
            result = ifcjs_viewer(ifc_file=ifc_bytes, height=600)
            
        with col2:
            st.subheader("Interaction Guide")
            st.markdown("""
            ### Navigation Modes
            - **Walk Mode**: Use WASD keys to move, Q/E to go up/down
            - **Select Mode**: Click on elements to view their properties
            - **Measure Mode**: Click two points to measure distance
            
            ### Selected Element Info
            """)
            
            if result and "type" in result:
                if result["type"] == "selection":
                    st.json({
                        "ID": result.get("globalId", "Unknown"),
                        "Type": result.get("type", "Unknown"),
                    })
                elif result["type"] == "measurement":
                    st.write(f"Measured distance: {result.get('distance', 0):.2f} meters")
