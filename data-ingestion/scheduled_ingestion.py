import schedule
import time
import os
from datetime import datetime
from scrape_njit_resources import NJITDataIngestion
from setup_index import AzureSearchIndexer
import json

class ScheduledIngestion:
    def __init__(self):
        self.scraper = NJITDataIngestion()
        self.indexer = AzureSearchIndexer()
    
    def run_ingestion(self):
        """Run the complete data ingestion process"""
        print(f"Starting scheduled ingestion at {datetime.now()}")
        
        try:
            # Scrape resources
            print("Scraping NJIT resources...")
            resources = self.scraper.scrape_all_resources()
            
            # Save to files
            self.scraper.save_to_json(resources, "njit_resources_latest.json")
            
            # Upload to Azure Search
            print("Uploading to Azure AI Search...")
            self.indexer.upload_documents(resources)
            
            # Update last indexed timestamp
            self.update_last_indexed()
            
            print(f"Ingestion completed successfully at {datetime.now()}")
            
        except Exception as e:
            print(f"Error during scheduled ingestion: {e}")
    
    def update_last_indexed(self):
        """Update the last indexed timestamp"""
        timestamp = datetime.now().isoformat()
        
        # Save timestamp to a file that can be read by the frontend
        with open("last_indexed.txt", "w") as f:
            f.write(timestamp)
        
        print(f"Last indexed timestamp updated: {timestamp}")

def main():
    """Main function to run scheduled ingestion"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    ingestion = ScheduledIngestion()
    
    # Schedule hourly ingestion
    schedule.every().hour.do(ingestion.run_ingestion)
    
    # Run initial ingestion
    print("Running initial ingestion...")
    ingestion.run_ingestion()
    
    # Keep the scheduler running
    print("Scheduler started. Running hourly ingestion...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
