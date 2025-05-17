// PDF.js Viewer for Streamlit with navigation, zoom, markup, and measurement tools
// First, create the Python Streamlit component to load this JS

'''python
import streamlit as st
import base64
from pathlib import Path

def pdf_viewer(pdf_file, width=800, height=600, key=None):
    """
    Embed a PDF viewer in Streamlit with advanced features.
    
    Parameters:
    -----------
    pdf_file : str or Path
        Path to the PDF file to display
    width : int
        Width of the viewer in pixels
    height : int
        Width of the viewer in pixels
    key : str
        Unique key for the component
        
    Returns:
    --------
    None
    """
    # Read the PDF file
    pdf_path = Path(pdf_file)
    if not pdf_path.exists():
        st.error(f"PDF file not found: {pdf_file}")
        return
    
    # Encode the PDF file to base64
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    # Create a data URL
    pdf_display = f'data:application/pdf;base64,{base64_pdf}'
    
    # Load the PDF.js libraries and CSS
    pdfjs_html = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.7.107/pdf.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.7.107/pdf.worker.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.7.107/pdf_viewer.min.css">
    
    <style>
        .pdf-container {
            border: 1px solid #ccc;
            position: relative;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        #pdf-viewer {
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: #525659;
        }
        
        #pdf-canvas {
            margin: 0 auto;
            display: block;
        }
        
        .toolbar {
            padding: 8px;
            background-color: #f0f0f0;
            border-bottom: 1px solid #ccc;
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .toolbar button, .toolbar select, .toolbar input {
            padding: 4px 8px;
            border: 1px solid #ccc;
            background: white;
            border-radius: 3px;
            cursor: pointer;
        }
        
        .toolbar button:hover {
            background-color: #e0e0e0;
        }
        
        .toolbar button.active {
            background-color: #d0d0d0;
            font-weight: bold;
        }
        
        .toolbar-section {
            display: flex;
            gap: 5px;
            align-items: center;
            margin-right: 10px;
        }
        
        #page-info {
            margin: 0 10px;
        }
        
        #annotation-container {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 2;
        }
        
        #annotation-container.drawing {
            pointer-events: auto;
            cursor: crosshair;
        }
        
        .annotation {
            position: absolute;
            pointer-events: auto;
        }
        
        .highlight {
            background-color: rgba(255, 255, 0, 0.3);
        }
        
        .drawing-path {
            stroke: red;
            stroke-width: 2;
            fill: none;
        }
        
        .measure-line {
            stroke: blue;
            stroke-width: 1;
            fill: none;
        }
        
        .measure-text {
            font-size: 10px;
            fill: blue;
            dominant-baseline: hanging;
        }
        
        .toolbar-label {
            display: inline-block;
            margin-right: 4px;
        }
    </style>
    
    <div class="toolbar">
        <div class="toolbar-section">
            <button id="prev-page"><span>&lt;</span> Prev</button>
            <span id="page-info">Page <span id="page-num"></span> of <span id="page-count"></span></span>
            <button id="next-page">Next <span>&gt;</span></button>
            <input type="number" id="page-jump" min="1" value="1" style="width: 50px;">
            <button id="go-btn">Go</button>
        </div>
        
        <div class="toolbar-section">
            <button id="zoom-out">−</button>
            <select id="zoom-select">
                <option value="0.5">50%</option>
                <option value="0.75">75%</option>
                <option value="1" selected>100%</option>
                <option value="1.25">125%</option>
                <option value="1.5">150%</option>
                <option value="2">200%</option>
                <option value="auto">Page Fit</option>
                <option value="width">Page Width</option>
            </select>
            <button id="zoom-in">+</button>
        </div>
        
        <div class="toolbar-section">
            <button id="tool-select" class="active">Select</button>
            <button id="tool-highlight">Highlight</button>
            <button id="tool-draw">Draw</button>
            <button id="tool-measure">Measure</button>
            <button id="tool-clear">Clear All</button>
        </div>
        
        <div class="toolbar-section" id="measure-tools" style="display: none;">
            <span class="toolbar-label">Scale:</span>
            <input type="number" id="scale-value" value="1" min="0.01" step="0.01" style="width: 50px;">
            <select id="scale-unit">
                <option value="mm">mm</option>
                <option value="cm">cm</option>
                <option value="in">in</option>
                <option value="ft">ft</option>
            </select>
            <span class="toolbar-label">per</span>
            <input type="number" id="scale-px" value="100" min="1" style="width: 50px;">
            <span class="toolbar-label">px</span>
        </div>
    </div>
    
    <div class="pdf-container" style="width: {width}px; height: {height}px;">
        <div id="pdf-viewer">
            <canvas id="pdf-canvas"></canvas>
        </div>
        <div id="annotation-container"></div>
    </div>
    
    <script>
        // Initialize the PDF.js worker
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.7.107/pdf.worker.min.js';
        
        // PDF variables
        let pdfDoc = null;
        let pageNum = 1;
        let pageRendering = false;
        let pageNumPending = null;
        let scale = 1.0;
        let canvas = document.getElementById('pdf-canvas');
        let ctx = canvas.getContext('2d');
        let pdfViewer = document.getElementById('pdf-viewer');
        let annotationContainer = document.getElementById('annotation-container');
        
        // Annotation variables
        let currentTool = 'select';
        let annotations = [];
        let isDrawing = false;
        let drawingPath = [];
        let measureStartPoint = null;
        let currentAnnotation = null;
        
        // Measurement scale variables
        let scaleValue = 1;
        let scaleUnit = 'mm';
        let scalePx = 100;
        
        // Load the PDF
        const loadPDF = async () => {
            const loadingTask = pdfjsLib.getDocument('{pdf_display}');
            try {{
                pdfDoc = await loadingTask.promise;
                document.getElementById('page-count').textContent = pdfDoc.numPages;
                document.getElementById('page-jump').max = pdfDoc.numPages;
                
                // Initially render first page
                renderPage(pageNum);
            }} catch (error) {{
                console.error('Error loading PDF:', error);
            }}
        };
        
        // Render a specific page
        const renderPage = (num) => {{
            pageRendering = true;
            
            // Get the page
            pdfDoc.getPage(num).then((page) => {{
                // Calculate the scale to fit the page width or height based on zoom setting
                let viewport;
                if (scale === 'auto') {{
                    // Fit page completely in the viewer
                    const containerWidth = pdfViewer.clientWidth;
                    const containerHeight = pdfViewer.clientHeight;
                    const hScale = containerWidth / page.getViewport({{scale: 1}}).width;
                    const vScale = containerHeight / page.getViewport({{scale: 1}}).height;
                    viewport = page.getViewport({{scale: Math.min(hScale, vScale) * 0.95}});
                }} else if (scale === 'width') {{
                    // Fit page width in the viewer
                    const containerWidth = pdfViewer.clientWidth;
                    const hScale = containerWidth / page.getViewport({{scale: 1}}).width;
                    viewport = page.getViewport({{scale: hScale * 0.95}});
                }} else {{
                    // Use specific scale value
                    viewport = page.getViewport({{scale: scale}});
                }}
                
                // Set canvas dimensions
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                
                // Render PDF page
                const renderContext = {{
                    canvasContext: ctx,
                    viewport: viewport
                }};
                
                page.render(renderContext).promise.then(() => {{
                    pageRendering = false;
                    
                    // Update page number display
                    document.getElementById('page-num').textContent = num;
                    document.getElementById('page-jump').value = num;
                    
                    // If another page rendering is pending, render that page
                    if (pageNumPending !== null) {{
                        renderPage(pageNumPending);
                        pageNumPending = null;
                    }}
                    
                    // Redraw annotations for the current page
                    redrawAnnotations();
                }});
            }});
        };
        
        // Queue rendering of a page
        const queueRenderPage = (num) => {{
            if (pageRendering) {{
                pageNumPending = num;
            }} else {{
                renderPage(num);
            }}
        }};
        
        // Go to previous page
        const onPrevPage = () => {{
            if (pageNum <= 1) {{
                return;
            }}
            pageNum--;
            queueRenderPage(pageNum);
        }};
        
        // Go to next page
        const onNextPage = () => {{
            if (pageNum >= pdfDoc.numPages) {{
                return;
            }}
            pageNum++;
            queueRenderPage(pageNum);
        }};
        
        // Go to a specific page
        const goToPage = () => {{
            const input = document.getElementById('page-jump');
            const pageRequested = parseInt(input.value);
            
            if (pageRequested >= 1 && pageRequested <= pdfDoc.numPages) {{
                pageNum = pageRequested;
                queueRenderPage(pageNum);
            }} else {{
                input.value = pageNum;
            }}
        }};
        
        // Handle zoom
        const handleZoom = (newScale) => {{
            scale = newScale;
            queueRenderPage(pageNum);
        }};
        
        // Create a new annotation
        const createAnnotation = (type, data) => {{
            const annotation = {{
                id: Date.now(),
                type: type,
                data: data,
                page: pageNum
            }};
            
            annotations.push(annotation);
            redrawAnnotations();
            return annotation;
        }};
        
        // Redraw all annotations for the current page
        const redrawAnnotations = () => {{
            // Clear previous annotations
            annotationContainer.innerHTML = '';
            
            // Create an SVG element for drawing annotations
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.position = 'absolute';
            svg.style.top = '0';
            svg.style.left = '0';
            svg.style.pointerEvents = 'none';
            annotationContainer.appendChild(svg);
            
            // Render annotations for the current page
            const pageAnnotations = annotations.filter(a => a.page === pageNum);
            
            pageAnnotations.forEach(annotation => {{
                if (annotation.type === 'highlight') {{
                    const div = document.createElement('div');
                    div.classList.add('annotation', 'highlight');
                    div.style.left = annotation.data.x + 'px';
                    div.style.top = annotation.data.y + 'px';
                    div.style.width = annotation.data.width + 'px';
                    div.style.height = annotation.data.height + 'px';
                    div.dataset.id = annotation.id;
                    annotationContainer.appendChild(div);
                }} else if (annotation.type === 'drawing') {{
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    let d = 'M ' + annotation.data[0].x + ' ' + annotation.data[0].y;
                    
                    for (let i = 1; i < annotation.data.length; i++) {{
                        d += ' L ' + annotation.data[i].x + ' ' + annotation.data[i].y;
                    }}
                    
                    path.setAttribute('d', d);
                    path.classList.add('drawing-path');
                    path.dataset.id = annotation.id;
                    svg.appendChild(path);
                }} else if (annotation.type === 'measure') {{
                    // Draw the measurement line
                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line.setAttribute('x1', annotation.data.x1);
                    line.setAttribute('y1', annotation.data.y1);
                    line.setAttribute('x2', annotation.data.x2);
                    line.setAttribute('y2', annotation.data.y2);
                    line.classList.add('measure-line');
                    svg.appendChild(line);
                    
                    // Calculate line length in pixels
                    const dx = annotation.data.x2 - annotation.data.x1;
                    const dy = annotation.data.y2 - annotation.data.y1;
                    const pixelLength = Math.sqrt(dx * dx + dy * dy);
                    
                    // Convert to measurement units
                    const measuredLength = (pixelLength / scalePx) * scaleValue;
                    const measuredLengthText = measuredLength.toFixed(2) + ' ' + scaleUnit;
                    
                    // Add measurement text
                    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    // Position text at midpoint of the line
                    const midX = (annotation.data.x1 + annotation.data.x2) / 2;
                    const midY = (annotation.data.y1 + annotation.data.y2) / 2;
                    text.setAttribute('x', midX);
                    text.setAttribute('y', midY - 5);  // Offset above the line
                    text.classList.add('measure-text');
                    text.textContent = measuredLengthText;
                    svg.appendChild(text);
                }}
            }});
        }};
        
        // Handle mouse events for annotations
        const startDrawing = (e) => {{
            if (currentTool === 'draw') {{
                isDrawing = true;
                drawingPath = [];
                
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                drawingPath.push({{x, y}});
                
                annotationContainer.classList.add('drawing');
            }} else if (currentTool === 'highlight') {{
                // Start highlighting
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                currentAnnotation = {{
                    startX: x,
                    startY: y
                }};
            }} else if (currentTool === 'measure') {{
                // Start measuring
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                if (!measureStartPoint) {{
                    measureStartPoint = {{x, y}};
                }} else {{
                    // Complete the measurement
                    createAnnotation('measure', {{
                        x1: measureStartPoint.x,
                        y1: measureStartPoint.y,
                        x2: x,
                        y2: y
                    }});
                    
                    measureStartPoint = null;
                }}
            }}
        }};
        
        const continueDrawing = (e) => {{
            if (isDrawing) {{
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                drawingPath.push({{x, y}});
                
                // Redraw the current path
                redrawDrawingPath();
            }} else if (currentTool === 'highlight' && currentAnnotation) {{
                // Update highlight size
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                // Create a temporary highlight element
                let highlightElem = document.querySelector('.temp-highlight');
                if (!highlightElem) {{
                    highlightElem = document.createElement('div');
                    highlightElem.classList.add('annotation', 'highlight', 'temp-highlight');
                    annotationContainer.appendChild(highlightElem);
                }}
                
                // Calculate the rectangle dimensions
                const left = Math.min(currentAnnotation.startX, x);
                const top = Math.min(currentAnnotation.startY, y);
                const width = Math.abs(x - currentAnnotation.startX);
                const height = Math.abs(y - currentAnnotation.startY);
                
                // Update the highlight element
                highlightElem.style.left = left + 'px';
                highlightElem.style.top = top + 'px';
                highlightElem.style.width = width + 'px';
                highlightElem.style.height = height + 'px';
            }} else if (currentTool === 'measure' && measureStartPoint) {{
                // Show temporary measurement line
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                // Redraw all annotations plus the temporary line
                redrawAnnotations();
                
                // Add the temporary measure line to the SVG
                const svg = annotationContainer.querySelector('svg');
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', measureStartPoint.x);
                line.setAttribute('y1', measureStartPoint.y);
                line.setAttribute('x2', x);
                line.setAttribute('y2', y);
                line.classList.add('measure-line');
                line.classList.add('temp-line');
                svg.appendChild(line);
                
                // Calculate and show the measurement
                const dx = x - measureStartPoint.x;
                const dy = y - measureStartPoint.y;
                const pixelLength = Math.sqrt(dx * dx + dy * dy);
                const measuredLength = (pixelLength / scalePx) * scaleValue;
                const measuredLengthText = measuredLength.toFixed(2) + ' ' + scaleUnit;
                
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                const midX = (measureStartPoint.x + x) / 2;
                const midY = (measureStartPoint.y + y) / 2;
                text.setAttribute('x', midX);
                text.setAttribute('y', midY - 5);
                text.classList.add('measure-text', 'temp-text');
                text.textContent = measuredLengthText;
                svg.appendChild(text);
            }}
        }};
        
        const endDrawing = (e) => {{
            if (isDrawing) {{
                isDrawing = false;
                annotationContainer.classList.remove('drawing');
                
                // Save the drawing path as an annotation
                if (drawingPath.length > 1) {{
                    createAnnotation('drawing', drawingPath);
                }}
                
                drawingPath = [];
            }} else if (currentTool === 'highlight' && currentAnnotation) {{
                // Save the highlight as an annotation
                const tempHighlight = document.querySelector('.temp-highlight');
                if (tempHighlight) {{
                    const rect = tempHighlight.getBoundingClientRect();
                    const canvasRect = canvas.getBoundingClientRect();
                    
                    const x = parseFloat(tempHighlight.style.left);
                    const y = parseFloat(tempHighlight.style.top);
                    const width = parseFloat(tempHighlight.style.width);
                    const height = parseFloat(tempHighlight.style.height);
                    
                    if (width > 5 && height > 5) {{
                        createAnnotation('highlight', {{x, y, width, height}});
                    }}
                    
                    tempHighlight.remove();
                }}
                
                currentAnnotation = null;
            }}
        }};
        
        // Draw the current path during mouse movement
        const redrawDrawingPath = () => {{
            if (drawingPath.length < 2) return;
            
            // Redraw all annotations
            redrawAnnotations();
            
            // Add the current drawing path to SVG
            const svg = annotationContainer.querySelector('svg');
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            
            let d = 'M ' + drawingPath[0].x + ' ' + drawingPath[0].y;
            for (let i = 1; i < drawingPath.length; i++) {{
                d += ' L ' + drawingPath[i].x + ' ' + drawingPath[i].y;
            }}
            
            path.setAttribute('d', d);
            path.classList.add('drawing-path', 'temp-path');
            svg.appendChild(path);
        }};
        
        // Switch between tools
        const setActiveTool = (tool) => {{
            currentTool = tool;
            
            // Remove active class from all tool buttons
            document.querySelectorAll('.toolbar button').forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Add active class to the selected tool button
            document.getElementById('tool-' + tool).classList.add('active');
            
            // Show/hide measure tools
            document.getElementById('measure-tools').style.display = (tool === 'measure') ? 'flex' : 'none';
            
            // Reset states
            isDrawing = false;
            drawingPath = [];
            currentAnnotation = null;
            measureStartPoint = null;
            annotationContainer.classList.remove('drawing');
            
            // Remove any temporary elements
            document.querySelectorAll('.temp-highlight, .temp-path, .temp-line, .temp-text').forEach(elem => {{
                elem.remove();
            }});
        }};
        
        // Clear all annotations
        const clearAnnotations = () => {{
            annotations = [];
            redrawAnnotations();
        }};
        
        // Update measurement scale
        const updateScale = () => {{
            scaleValue = parseFloat(document.getElementById('scale-value').value);
            scaleUnit = document.getElementById('scale-unit').value;
            scalePx = parseFloat(document.getElementById('scale-px').value);
            
            // Redraw annotations to update measurements
            redrawAnnotations();
        }};
        
        // Set up event listeners
        document.getElementById('prev-page').addEventListener('click', onPrevPage);
        document.getElementById('next-page').addEventListener('click', onNextPage);
        document.getElementById('go-btn').addEventListener('click', goToPage);
        document.getElementById('page-jump').addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') goToPage();
        }});
        
        document.getElementById('zoom-in').addEventListener('click', () => {{
            const zoomSelect = document.getElementById('zoom-select');
            const currentIndex = zoomSelect.selectedIndex;
            if (currentIndex < zoomSelect.options.length - 1) {{
                zoomSelect.selectedIndex = currentIndex + 1;
                handleZoom(zoomSelect.value);
            }}
        }});
        
        document.getElementById('zoom-out').addEventListener('click', () => {{
            const zoomSelect = document.getElementById('zoom-select');
            const currentIndex = zoomSelect.selectedIndex;
            if (currentIndex > 0) {{
                zoomSelect.selectedIndex = currentIndex - 1;
                handleZoom(zoomSelect.value);
            }}
        }});
        
        document.getElementById('zoom-select').addEventListener('change', (e) => {{
            handleZoom(e.target.value);
        }});
        
        // Tool selection
        document.getElementById('tool-select').addEventListener('click', () => setActiveTool('select'));
        document.getElementById('tool-highlight').addEventListener('click', () => setActiveTool('highlight'));
        document.getElementById('tool-draw').addEventListener('click', () => setActiveTool('draw'));
        document.getElementById('tool-measure').addEventListener('click', () => setActiveTool('measure'));
        document.getElementById('tool-clear').addEventListener('click', clearAnnotations);
        
        // Measurement scale controls
        document.getElementById('scale-value').addEventListener('change', updateScale);
        document.getElementById('scale-unit').addEventListener('change', updateScale);
        document.getElementById('scale-px').addEventListener('change', updateScale);
        
        // Drawing events
        annotationContainer.addEventListener('mousedown', startDrawing);
        annotationContainer.addEventListener('mousemove', continueDrawing);
        annotationContainer.addEventListener('mouseup', endDrawing);
        
        // Initialize
        loadPDF();
    </script>
    """
    
    # Display the HTML component
    st.components.v1.html(pdfjs_html, width=width, height=height + 50, scrolling=False)

# Example usage
st.title("Advanced PDF Viewer with Markup and Measurement")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    # Save the uploaded file to a temporary location
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        pdf_path = tmp_file.name
    
    # Display settings
    with st.expander("Display Settings"):
        col1, col2 = st.columns(2)
        with col1:
            width = st.number_input("Viewer Width", min_value=400, max_value=2000, value=800)
        with col2:
            height = st.number_input("Viewer Height", min_value=400, max_value=2000, value=600)
    
    # Render the PDF viewer
    pdf_viewer(pdf_path, width=width, height=height)
    
    # Clean up the temporary file when the app is done
    def cleanup():
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
    
    # Register the cleanup function
    import atexit
    atexit.register(cleanup)
else:
    st.info("Please upload a PDF file to view it with the advanced viewer.")
'''
