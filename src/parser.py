# src/parser.py
import logging
import html
import re
from pathlib import Path

class WikitionaryParser:
    """
    Parser for Wiktionary markup that delegates all template/module processing to
    Wiktionary's own templates and modules via the Lua engine.
    """
    
    def __init__(self, downloader, lua_engine):
        """Initialize with a template downloader and Lua engine."""
        self.downloader = downloader
        self.lua_engine = lua_engine
        self.logger = logging.getLogger(__name__)
    
    def parse(self, raw_text: str) -> str:
        """Parse raw Wiktionary markup into processed text."""
        try:
            # Ensure all required templates and modules are downloaded
            self._ensure_dependencies_downloaded(raw_text)
            
            # Process the text using the Lua engine 
            processed_text = self.lua_engine.process_wikitext(raw_text)
            
            # Process HTML entities
            processed_text = html.unescape(processed_text)
            
            # Clean up any remaining markup
            processed_text = self._clean_output(processed_text)
            
            return processed_text
        
        except Exception as e:
            self.logger.error(f"Error parsing wikitext: {str(e)}")
            return self._fallback_parse(raw_text)
    
    def _ensure_dependencies_downloaded(self, text: str) -> None:
        """Extract and ensure all templates and modules are downloaded."""
        # Extract and download templates
        templates = self.downloader.extract_template_names(text)
        for template in templates:
            self.downloader.download_template(template)
        
        # Extract and download modules
        modules = self.downloader.extract_module_names(text)
        for module in modules:
            self.downloader.download_module(module)
    
    def _fallback_parse(self, raw_text: str) -> str:
        """
        Very minimal fallback parsing as a last resort when Lua processing fails.
        This is just a safety net and doesn't attempt to implement any Wiktionary template logic.
        """
        # Basic wikilink processing
        text = re.sub(r'\[\[([^|\]]+?)(?:\|([^\]]+?))?\]\]', 
                     lambda m: m.group(2) if m.group(2) else m.group(1), 
                     raw_text)
        
        # HTML entities
        text = html.unescape(text)
        
        # Remove templates as a last resort
        text = re.sub(r'\{\{[^}]+\}\}', '', text)
        
        # Clean up
        text = self._clean_output(text)
        
        return text
    
    def _clean_output(self, text: str) -> str:
        """Clean up the processed output."""
        # Remove any remaining wiki markup
        text = re.sub(r'\{\{[^}]+\}\}', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text