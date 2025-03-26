import os
import requests
import logging
import json
import time
import re
from urllib.parse import quote

class TemplateManager:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.logger = logging.getLogger('wiktionary_processor')
        self.downloaded_items = set()
        self.failed_items = set()
        
        # Create cache directories if they don't exist
        os.makedirs(os.path.join(cache_dir, 'Template'), exist_ok=True)
        os.makedirs(os.path.join(cache_dir, 'Module'), exist_ok=True)
        
    def download_item(self, item_type, item_name):
        """Download a template or module from Wiktionary API"""
        # Check if we already tried to download this item
        item_key = f"{item_type}:{item_name}"
        if item_key in self.downloaded_items or item_key in self.failed_items:
            return

        try:
            self.logger.info(f"Downloading {item_type}: {item_name}")
            
            # Determine the appropriate namespace prefix
            namespace = item_type
            
            # Construct the API URL
            api_url = f"https://en.wiktionary.org/w/api.php"
            
            # Get the content of the template/module
            params = {
                'action': 'query',
                'titles': f"{namespace}:{item_name}",
                'prop': 'revisions',
                'rvprop': 'content',
                'format': 'json'
            }
            
            response = requests.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Process the response
            pages = data.get('query', {}).get('pages', {})
            
            if pages:
                # Get the first (and should be only) page
                page_id = next(iter(pages))
                page = pages[page_id]
                
                # Check if the page exists
                if 'missing' in page:
                    self.logger.warning(f"{item_type} {item_name} not found on Wiktionary")
                    self.failed_items.add(item_key)
                    return
                
                revisions = page.get('revisions', [])
                if revisions:
                    content = revisions[0].get('*', '')
                    
                    # Save the content to the cache
                    self._save_to_cache(item_type, item_name, content)
                    self.downloaded_items.add(item_key)
                    
                    # Check for dependencies in the content
                    self._check_for_dependencies(content)
                else:
                    self.logger.warning(f"No revisions found for {item_type} {item_name}")
                    self.failed_items.add(item_key)
            else:
                self.logger.warning(f"No pages found for {item_type} {item_name}")
                self.failed_items.add(item_key)
                
        except Exception as e:
            self.logger.error(f"Error downloading {item_type} {item_name}: {str(e)}")
            self.failed_items.add(item_key)
    
    def _save_to_cache(self, item_type, item_name, content):
        """Save template/module content to cache"""
        try:
            # Sanitize the filename
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', item_name)
            
            # Create the file path
            file_path = os.path.join(self.cache_dir, item_type, f"{safe_name}.txt")
            
            # Save the content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.logger.info(f"Saved {item_type} {item_name} to cache")
            
        except Exception as e:
            self.logger.error(f"Error saving {item_type} {item_name} to cache: {str(e)}")
    
    def _check_for_dependencies(self, content):
        """Check for dependencies in the content and download them"""
        # Look for template dependencies
        template_pattern = r'{{([^}|]+)'
        template_matches = re.findall(template_pattern, content)
        
        for template in template_matches:
            # Clean up the template name
            template = template.strip()
            
            # Skip some common non-template uses of double braces
            if template.lower() in ['if', 'ifeq', 'switch', 'for', '#invoke']:
                continue
                
            self.download_item('Template', template)
        
        # Look for module dependencies
        module_pattern = r'require\s*\(\s*["\']Module:([^"\']+)["\']'
        module_matches = re.findall(module_pattern, content)
        
        for module in module_matches:
            # Clean up the module name
            module = module.strip()
            self.download_item('Module', module)
    
    def generate_summary_report(self):
        """Generate a summary report of downloaded and failed items"""
        report_path = os.path.join(self.cache_dir, 'download_report.json')
        
        report = {
            'downloaded_items': list(self.downloaded_items),
            'failed_items': list(self.failed_items),
            'total_downloaded': len(self.downloaded_items),
            'total_failed': len(self.failed_items)
        }
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
                
            self.logger.info(f"Generated download report: {report_path}")
            self.logger.info(f"Total items downloaded: {len(self.downloaded_items)}, failed: {len(self.failed_items)}")
            
        except Exception as e:
            self.logger.error(f"Error generating download report: {str(e)}")