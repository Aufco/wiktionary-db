import requests
import logging
import re
import time
import json
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
            wikitext = f"<div>{raw_text}</div>"
            
            self.logger.info(f"Sending request to MediaWiki API at: {self.api_url}")
            self.logger.info(f"Input wikitext: {wikitext}")
            
            # Make API request to parse the wikitext
            response = requests.post(
                self.api_url,
                data={
                    'action': 'parse',
                    'text': wikitext,
                    'contentmodel': 'wikitext',
                    'format': 'json',
                    'disablelimitreport': 1,
                    'prop': 'text'
                },
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                timeout=30
            )
            
            # Log response details
            self.logger.info(f"Response status code: {response.status_code}")
            self.logger.info(f"Response headers: {response.headers}")
            
            # Log the raw response content (first 200 chars)
            content_preview = response.content[:200] if response.content else b"(empty)"
            self.logger.info(f"Raw response content (first 200 chars): {content_preview}")
            
            response.raise_for_status()
            
            # Try multiple parsing approaches
            result = None
            parsing_errors = []
            
            # Approach 1: Handle UTF-8 BOM
            try:
                content = response.content.decode('utf-8-sig')
                result = json.loads(content)
                self.logger.info("Successfully parsed response with utf-8-sig encoding")
            except Exception as e:
                parsing_errors.append(f"UTF-8-sig parsing failed: {str(e)}")
            
            # Approach 2: Standard JSON parsing
            if result is None:
                try:
                    result = response.json()
                    self.logger.info("Successfully parsed response with standard json()")
                except Exception as e:
                    parsing_errors.append(f"Standard JSON parsing failed: {str(e)}")
            
            # Approach 3: Try to extract JSON from HTML error response
            if result is None and b'<' in response.content:
                try:
                    # Some error responses might contain HTML
                    error_text = response.content.decode('utf-8-sig')
                    self.logger.error(f"Received HTML error response: {error_text[:200]}...")
                    return f"ERROR: MediaWiki API returned HTML error"
                except Exception as e:
                    parsing_errors.append(f"HTML parsing failed: {str(e)}")
            
            # If all parsing attempts failed
            if result is None:
                error_msg = "; ".join(parsing_errors)
                self.logger.error(f"All JSON parsing attempts failed. Error: {error_msg}")
                return f"ERROR: Failed to parse MediaWiki API response - {error_msg}"
            
            # Extract the parsed HTML if successful
            if 'parse' in result and 'text' in result['parse']:
                html = result['parse']['text']['*']
                cleaned_text = self._clean_html(html)
                return cleaned_text
            else:
                # For now, if result doesn't contain parsed text, return raw definition
                # This helps us see if API is working at all
                self.logger.warning(f"API response did not contain parsed text: {result}")
                return f"PROCESSING ERROR - USING RAW: {raw_text}"
                
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