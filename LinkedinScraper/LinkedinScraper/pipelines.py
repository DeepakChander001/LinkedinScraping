import json
import os
from itemadapter import ItemAdapter


class LinkedinScraperPipeline:
    def __init__(self):
        # Create data directory if it doesn't exist
        self.data_dir = 'linkedin_data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Initialize the users list
        self.users = []
        
        # Output file path
        self.output_file = os.path.join(self.data_dir, 'linkedin_profiles.json')
    
    def process_item(self, item, spider):
        """Process each scraped item"""
        adapter = ItemAdapter(item)
        
        # Clean and format data if needed
        self._clean_item(adapter)
        
        # Add processed item to our list
        self.users.append(dict(adapter))
        
        # Return the item for potential further processing
        return item
    
    def _clean_item(self, adapter):
        """Clean and format the item data"""
        # Clean name
        if adapter.get('name'):
            adapter['name'] = adapter['name'].strip()
        
        # Clean title
        if adapter.get('title'):
            adapter['title'] = adapter['title'].strip()
        
        # Clean location
        if adapter.get('location'):
            adapter['location'] = adapter['location'].strip()
    
    def close_spider(self, spider):
        """Called when spider is closed, save all data to JSON file"""
        # Save data to JSON file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=4)
        
        spider.logger.info(f"Saved {len(self.users)} profiles to {self.output_file}")


class CsvExportPipeline:
    """Export data to CSV file"""
    def __init__(self):
        # Create data directory if it doesn't exist
        self.data_dir = 'linkedin_data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Output file path
        self.csv_file = os.path.join(self.data_dir, 'linkedin_profiles.csv')
        self.csv_experience_file = os.path.join(self.data_dir, 'linkedin_experiences.csv')
        
        # CSV headers
        self.profile_headers = ['url', 'name', 'title', 'location', 'summary']
        self.experience_headers = ['profile_url', 'name', 'role', 'company', 'start_date', 'end_date', 'duration', 'description']
        
        # Initialize CSV files
        self._init_csv_files()
    
    def _init_csv_files(self):
        """Initialize CSV files with headers"""
        import csv
        
        # Create profiles CSV file with headers
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.profile_headers)
        
        # Create experiences CSV file with headers
        with open(self.csv_experience_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.experience_headers)
    
    def process_item(self, item, spider):
        """Process each item and write to CSV files"""
        import csv
        
        adapter = ItemAdapter(item)
        
        # Write basic profile info to profiles CSV
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Extract values for each header
            row = [adapter.get(header, '') for header in self.profile_headers]
            writer.writerow(row)
        
        # Write experience info to experiences CSV
        if adapter.get('experience'):
            with open(self.csv_experience_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                for exp in adapter.get('experience'):
                    # Create a row for each experience entry
                    row = [
                        adapter.get('url', ''),
                        adapter.get('name', ''),
                        exp.get('role', ''),
                        exp.get('company', ''),
                        exp.get('start_date', ''),
                        exp.get('end_date', ''),
                        exp.get('duration', ''),
                        exp.get('description', '')
                    ]
                    writer.writerow(row)
        
        return item 