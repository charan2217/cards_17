import streamlit as st
import os
import pandas as pd
from datetime import datetime
from ocr_module import extract_text
from nlp_module import extract_entities
from database_module import save_to_database, get_database_stats, export_database_backup

# Configure page
st.set_page_config(
    page_title="AI Business Card Scanner",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #366092;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .warning-message {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📸 AI Business Card Scanner</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📊 Database Stats")
    
    try:
        stats = get_database_stats()
        if "error" not in stats:
            st.metric("Total Entries", stats["total_entries"])
            st.metric("Active Entries", stats["active_entries"])
            st.caption(f"Last Updated: {stats['last_updated']}")
        else:
            st.error("Database error")
    except:
        st.error("Could not load stats")
    
    st.markdown("---")
    
    st.header("🔧 Actions")
    if st.button("📥 Create Backup", help="Export database backup"):
        backup_status = export_database_backup()
        if "✅" in backup_status:
            st.success(backup_status)
        else:
            st.error(backup_status)
    
    st.markdown("---")
    st.header("📁 Auto-Monitoring")
    st.info("👀 Run `python watcher.py` in terminal to enable automatic card processing")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📤 Upload Business Card")
    
    uploaded_file = st.file_uploader(
        "Choose a business card image",
        type=["jpg", "png", "jpeg", "webp", "bmp", "tiff"],
        help="Supported formats: JPG, PNG, WebP, BMP, TIFF"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Display uploaded image
        st.image(uploaded_file, caption="Uploaded Business Card", use_column_width=True)
        
        # Process button
        if st.button("🔍 Extract Information", type="primary"):
            with st.spinner("Processing... This may take a few seconds"):
                try:
                    # Save uploaded file
                    folder = "cards"
                    if not os.path.exists(folder):
                        os.makedirs(folder)
                    
                    temp_path = os.path.join(folder, uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # OCR Extraction
                    st.info("🔍 Extracting text from image...")
                    text = extract_text(temp_path)
                    
                    if text.strip():
                        st.success(f"✅ Text extracted: {len(text)} characters")
                        
                        # NLP Extraction
                        st.info("🧠 Analyzing and extracting information...")
                        data = extract_entities(text)
                        
                        # Save to Database
                        st.info("💾 Saving to database...")
                        status = save_to_database(data)
                        
                        # Display results
                        st.markdown("### 📋 Extracted Information")
                        
                        # Display in a nice format
                        for field, value in data.items():
                            if value and value.strip():
                                st.markdown(f"**{field}:** {value}")
                        
                        # Special formatting for website
                        if data.get("Website"):
                            st.markdown(f"**Website:** [{data['Website']}]({data['Website']})")
                        
                        # Status message
                        if "✅" in status:
                            st.markdown(f'<div class="success-message">{status}</div>', unsafe_allow_html=True)
                        elif "⚠️" in status:
                            st.markdown(f'<div class="warning-message">{status}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="error-message">{status}</div>', unsafe_allow_html=True)
                        
                        # Clean up
                        os.remove(temp_path)
                        
                    else:
                        st.error("❌ No text could be extracted from the image. Please try with a clearer image.")
                        
                except Exception as e:
                    st.error(f"❌ Error processing image: {str(e)}")

with col2:
    st.header("📄 Extracted Text Preview")
    
    if uploaded_file:
        if st.button("🔄 Refresh Text Preview"):
            st.rerun()
    else:
        st.info("Upload an image to see extracted text here")
    
    # Display raw extracted text if available
    if 'text' in locals() and text:
        st.text_area("Raw OCR Text:", text, height=300)
        
        # Download text option
        st.download_button(
            label="📥 Download Text",
            data=text,
            file_name=f"extracted_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

# Instructions section
st.markdown("---")
st.header("📖 How to Use")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📸 Step 1: Upload
    - Upload a clear business card image
    - Supported formats: JPG, PNG, WebP
    - Ensure good lighting and focus
    """)

with col2:
    st.markdown("""
    ### 🔍 Step 2: Process
    - Click "Extract Information"
    - AI extracts text using dual OCR engines
    - NLP analyzes and categorizes data
    """)

with col3:
    st.markdown("""
    ### 💾 Step 3: Save
    - Data automatically saved to Excel
    - Duplicate entries are detected
    - Professional formatting applied
    """)

# Features section
st.markdown("---")
st.header("✨ Features")

features = [
    "🎯 **High Accuracy**: Dual OCR engines (EasyOCR + Tesseract) with advanced preprocessing",
    "🧠 **Smart Extraction**: AI-powered field recognition and categorization",
    "💾 **Auto Database**: Professional Excel database with duplicate detection",
    "👀 **Auto Monitoring**: Real-time folder monitoring for automatic processing",
    "📊 **Professional Format**: Color-coded Excel with validation and formatting",
    "🔒 **Data Integrity**: Backup functionality and error handling"
]

for feature in features:
    st.markdown(f"- {feature}")

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666;">'
    '🚀 AI Business Card Scanner | Built with Streamlit, EasyOCR, spaCy & Pandas'
    '</div>',
    unsafe_allow_html=True
)