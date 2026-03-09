from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import logging
from datetime import datetime
from ocr_module import extract_text
from nlp_module import extract_entities
from database_module import save_to_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('card_scanner.log'),
        logging.StreamHandler()
    ]
)

class CardHandler(FileSystemEventHandler):
    """Enhanced file system event handler for visiting card processing"""
    
    def __init__(self):
        self.processed_files = set()
        self.processing_delay = 2  # seconds to wait before processing new files
        
    def on_created(self, event):
        """Handle new file creation events"""
        if event.is_directory:
            return
            
        if event.src_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")):
            # Wait for file to be fully written
            time.sleep(self.processing_delay)
            
            # Check if file still exists and hasn't been processed
            if os.path.exists(event.src_path) and event.src_path not in self.processed_files:
                self.process_card(event.src_path)
    
    def on_moved(self, event):
        """Handle file move events (e.g., from camera app)"""
        if event.is_directory:
            return
            
        if event.dest_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")):
            time.sleep(self.processing_delay)
            
            if os.path.exists(event.dest_path) and event.dest_path not in self.processed_files:
                self.process_card(event.dest_path)
    
    def process_card(self, file_path):
        """Process a visiting card image"""
        try:
            filename = os.path.basename(file_path)
            logging.info(f"📸 Processing new card: {filename}")
            
            # Mark as being processed
            self.processed_files.add(file_path)
            
            # Step 1: Extract text using OCR
            logging.info("🔍 Extracting text from image...")
            extracted_text = extract_text(file_path)
            
            if not extracted_text.strip():
                logging.warning(f"⚠️ No text extracted from {filename}")
                return
            
            logging.info(f"✅ Text extracted: {len(extracted_text)} characters")
            
            # Step 2: Extract entities using NLP
            logging.info("🧠 Analyzing text and extracting information...")
            extracted_data = extract_entities(extracted_text)
            
            # Step 3: Save to database
            logging.info("💾 Saving to database...")
            save_status = save_to_database(extracted_data)
            
            logging.info(f"📊 Result: {save_status}")
            
            # Optional: Move processed file to processed folder
            self.archive_processed_file(file_path)
            
        except Exception as e:
            logging.error(f"❌ Error processing {file_path}: {str(e)}")
    
    def archive_processed_file(self, file_path):
        """Move processed file to archive folder"""
        try:
            processed_folder = "cards/processed"
            if not os.path.exists(processed_folder):
                os.makedirs(processed_folder)
            
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{filename}"
            new_path = os.path.join(processed_folder, new_filename)
            
            os.rename(file_path, new_path)
            logging.info(f"📁 Archived: {filename} -> {new_filename}")
            
        except Exception as e:
            logging.warning(f"⚠️ Could not archive file: {str(e)}")

def start_watcher():
    """Start the file system watcher"""
    cards_folder = "cards"
    
    # Ensure cards folder exists
    if not os.path.exists(cards_folder):
        os.makedirs(cards_folder)
        logging.info(f"📁 Created monitoring folder: {cards_folder}")
    
    # Initialize database
    from database_module import initialize_database
    db_status = initialize_database()
    logging.info(f"💾 Database: {db_status}")
    
    # Set up observer
    event_handler = CardHandler()
    observer = Observer()
    observer.schedule(event_handler, path=cards_folder, recursive=True)
    
    # Start monitoring
    observer.start()
    logging.info(f"👀 Started monitoring folder: {os.path.abspath(cards_folder)}")
    logging.info("📸 Add new visiting card images to the 'cards' folder for automatic processing")
    logging.info("⏹️ Press Ctrl+C to stop monitoring")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("🛑 Stopping file watcher...")
        observer.stop()
    
    observer.join()
    logging.info("✅ File watcher stopped")

if __name__ == "__main__":
    start_watcher()