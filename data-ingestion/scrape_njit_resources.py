import requests
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any
import json

class NJITDataIngestion:
    def __init__(self):
        self.base_urls = {
            "highlander_hub": "https://highlanderhub.njit.edu",
            "handshake": "https://njit.joinhandshake.com",
            "scholarship_universe": "https://njit.scholarshipuniverse.com",
            "tutoring": "https://www.njit.edu/academics/tutoring",
            "wellness": "https://www.njit.edu/student-life/health-wellness",
            "career_services": "https://www.njit.edu/career-services"
        }
        
        self.resources = []
    
    def scrape_highlander_hub_events(self) -> List[Dict[str, Any]]:
        """Scrape events from Highlander Hub"""
        events = []
        
        try:
            # This would be replaced with actual scraping logic
            # For demo purposes, creating sample events
            sample_events = [
                {
                    "title": "Women in STEM Networking Event",
                    "description": "Connect with successful women in STEM fields",
                    "date": "2024-02-15",
                    "time": "6:00 PM",
                    "location": "Campus Center",
                    "url": "https://highlanderhub.njit.edu/events/123",
                    "source": "highlander_hub",
                    "category": "events"
                },
                {
                    "title": "Study Group: Data Structures",
                    "description": "Collaborative study session for CS 114",
                    "date": "2024-02-20",
                    "time": "7:00 PM",
                    "location": "Library Study Room 3",
                    "url": "https://highlanderhub.njit.edu/events/124",
                    "source": "highlander_hub",
                    "category": "academics"
                }
            ]
            
            events.extend(sample_events)
            
        except Exception as e:
            print(f"Error scraping Highlander Hub events: {e}")
        
        return events
    
    def scrape_handshake_jobs(self) -> List[Dict[str, Any]]:
        """Scrape job listings from Handshake"""
        jobs = []
        
        try:
            # Sample job listings for demo
            sample_jobs = [
                {
                    "title": "Software Engineering Intern",
                    "company": "Tech Corp",
                    "description": "Summer internship for computer science students",
                    "location": "Remote",
                    "url": "https://njit.joinhandshake.com/jobs/456",
                    "source": "handshake",
                    "category": "career",
                    "deadline": "2024-03-01"
                },
                {
                    "title": "Data Analyst Position",
                    "company": "Analytics Inc",
                    "description": "Entry-level position for recent graduates",
                    "location": "Newark, NJ",
                    "url": "https://njit.joinhandshake.com/jobs/457",
                    "source": "handshake",
                    "category": "career",
                    "deadline": "2024-03-15"
                }
            ]
            
            jobs.extend(sample_jobs)
            
        except Exception as e:
            print(f"Error scraping Handshake jobs: {e}")
        
        return jobs
    
    def scrape_academic_resources(self) -> List[Dict[str, Any]]:
        """Scrape academic support resources"""
        resources = []
        
        try:
            sample_resources = [
                {
                    "title": "Math Tutoring Center",
                    "description": "Free tutoring for all math courses",
                    "url": "https://www.njit.edu/academics/tutoring/math",
                    "source": "tutoring",
                    "category": "academics",
                    "hours": "Mon-Fri 9AM-5PM"
                },
                {
                    "title": "Writing Center",
                    "description": "Help with essays, reports, and presentations",
                    "url": "https://www.njit.edu/academics/tutoring/writing",
                    "source": "tutoring",
                    "category": "academics",
                    "hours": "Mon-Thu 10AM-8PM"
                }
            ]
            
            resources.extend(sample_resources)
            
        except Exception as e:
            print(f"Error scraping academic resources: {e}")
        
        return resources
    
    def scrape_wellness_resources(self) -> List[Dict[str, Any]]:
        """Scrape wellness and mental health resources"""
        resources = []
        
        try:
            sample_resources = [
                {
                    "title": "Counseling Center",
                    "description": "Free confidential counseling services",
                    "url": "https://www.njit.edu/student-life/health-wellness/counseling",
                    "source": "wellness",
                    "category": "wellness",
                    "phone": "(973) 596-3414"
                },
                {
                    "title": "Stress Management Workshop",
                    "description": "Learn techniques to manage academic stress",
                    "url": "https://www.njit.edu/student-life/health-wellness/stress-management",
                    "source": "wellness",
                    "category": "wellness",
                    "schedule": "Every Tuesday 2PM"
                }
            ]
            
            resources.extend(sample_resources)
            
        except Exception as e:
            print(f"Error scraping wellness resources: {e}")
        
        return resources
    
    def scrape_all_resources(self) -> List[Dict[str, Any]]:
        """Scrape all NJIT resources"""
        all_resources = []
        
        print("Scraping Highlander Hub events...")
        all_resources.extend(self.scrape_highlander_hub_events())
        
        print("Scraping Handshake jobs...")
        all_resources.extend(self.scrape_handshake_jobs())
        
        print("Scraping academic resources...")
        all_resources.extend(self.scrape_academic_resources())
        
        print("Scraping wellness resources...")
        all_resources.extend(self.scrape_wellness_resources())
        
        # Add metadata
        for resource in all_resources:
            resource["scraped_at"] = datetime.now().isoformat()
            resource["id"] = f"{resource['source']}_{hash(resource['url'])}"
        
        return all_resources
    
    def save_to_csv(self, resources: List[Dict[str, Any]], filename: str = "njit_resources.csv"):
        """Save resources to CSV file"""
        df = pd.DataFrame(resources)
        df.to_csv(filename, index=False)
        print(f"Saved {len(resources)} resources to {filename}")
    
    def save_to_json(self, resources: List[Dict[str, Any]], filename: str = "njit_resources.json"):
        """Save resources to JSON file"""
        with open(filename, 'w') as f:
            json.dump(resources, f, indent=2)
        print(f"Saved {len(resources)} resources to {filename}")

if __name__ == "__main__":
    scraper = NJITDataIngestion()
    
    print("Starting NJIT resource scraping...")
    resources = scraper.scrape_all_resources()
    
    print(f"Scraped {len(resources)} total resources")
    
    # Save to files
    scraper.save_to_csv(resources)
    scraper.save_to_json(resources)
    
    print("Scraping completed!")
