import requests
import logging
import re
import time
from urllib.parse import quote

class WikiProcessor:
    def __init__(self, api_url, template_manager):
        self.api_url = api_url
        self.template_manager = template_manager
        self.logger = logging.getLogger('wiktionary_processor')
        
    def process_definition(self, raw_text):
        """Process a raw definition text using MediaWiki API"""
        # First, attempt to process with what we have
        processed_text = self._try_process_definition(raw_text)
        
        # Check for missing template or module errors
        missing_items = self._extract_missing_items(processed_text)
        
        # If there are missing templates/modules, download them and retry
        retry_count = 0
        max_retries = 5
        
        while missing_items and retry_count < max_retries:
            retry_count += 1
            self.logger.info(f"Found missing items: {missing_items}. Retry attempt {retry_count}")
            
            # Download all missing templates and modules
            for item_type, item_name in missing_items:
                self.template_manager.download_item(item_type, item_name)
                
            # Retry processing
            processed_text = self._try_process_definition(raw_text)
            
            # Check for any new missing items
            missing_items = self._extract_missing_items(processed_text)
        
        if missing_items:
            self.logger.warning(f"Still have missing items after {max_retries} retries: {missing_items}")
            processed_text = f"ERROR: Could not process due to missing items: {missing_items}"
        
        return processed_text
        
    def _try_process_definition(self, raw_text):
        """Attempt to process the definition with MediaWiki"""
        try:
            # Prepare the definition text for processing
            # Wrap it in a div to ensure proper parsing
            wikitext = f"<div>{raw_text}</div>"
            
            # Make API request to parse the wikitext
            response = requests.post(
                self.api_url,
                data={
                    'action': 'parse',
                    'text': wikitext,
                    'contentmodel': 'wikitext',
                    'format': 'json',
                    'prop': 'text'
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the parsed HTML
            if 'parse' in result and 'text' in result['parse']:
                html = result['parse']['text']['*']
                
                # Clean up the HTML to get plain text
                cleaned_text = self._clean_html(html)
                return cleaned_text
            else:
                self.logger.error(f"Unexpected API response format: {result}")
                return f"ERROR: Unexpected API response format"
                
        except requests.RequestException as e:
            self.logger.error(f"API request error: {e}")
            return f"ERROR: API request failed - {str(e)}"
            
        except Exception as e:
            self.logger.error(f"Processing error: {e}")
            return f"ERROR: {str(e)}"
    
    def _extract_missing_items(self, text):
        """Extract references to missing templates or modules from error text"""
        missing_items = []
        
        # Look for template errors
        template_pattern = r"Template:([^\s]+) not found"
        template_matches = re.findall(template_pattern, text)
        for template in template_matches:
            missing_items.append(('Template', template))
            
        # Look for module errors
        module_pattern = r"Module:([^\s]+) not found"
        module_matches = re.findall(module_pattern, text)
        for module in module_matches:
            missing_items.append(('Module', module))
            
        # Look for Lua errors that might indicate missing modules
        lua_pattern = r"Lua error in Module:([^\s:]+)"
        lua_matches = re.findall(lua_pattern, text)
        for module in lua_matches:
            if ('Module', module) not in missing_items:
                missing_items.append(('Module', module))
                
        return missing_items
    
    def _clean_html(self, html):
        """Clean HTML to get plain text"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
