# src/processor.py
import logging
from typing import Dict, Set, Optional, Tuple
import time

class DefinitionProcessor:
    """Process Wiktionary definitions using Wiktionary's own templates and modules."""
    
    def __init__(self, downloader, parser, lua_engine):
        """Initialize with a downloader, parser, and Lua engine."""
        self.downloader = downloader
        self.parser = parser
        self.lua_engine = lua_engine
        self.logger = logging.getLogger(__name__)
        
        # Track definitions with pending dependencies
        self.pending_definitions = {}
        
        # Statistics
        self.stats = {
            "processed_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "retry_count": 0,
            "template_usage": {},
            "module_usage": {},
        }
    
    def process_definition(self, word: str, raw_text: str) -> Optional[str]:
        """Process a raw definition text."""
        self.logger.debug(f"Processing definition for word: {word}")
        self.stats["processed_count"] += 1
        
        # Extract templates and modules used in this definition
        templates = self.downloader.extract_template_names(raw_text)
        modules = self.downloader.extract_module_names(raw_text)
        
        # Update usage statistics
        for template in templates:
            self.stats["template_usage"][template] = self.stats["template_usage"].get(template, 0) + 1
        
        for module in modules:
            self.stats["module_usage"][module] = self.stats["module_usage"].get(module, 0) + 1
        
        # Try to download missing templates and modules
        missing_templates = set()
        missing_modules = set()
        
        for template in templates:
            if not self.downloader.download_template(template):
                missing_templates.add(template)
        
        for module in modules:
            if not self.downloader.download_module(module):
                missing_modules.add(module)
        
        # If there are missing dependencies, store for retry later
        if missing_templates or missing_modules:
            def_key = f"{word}:{raw_text}"
            self.pending_definitions[def_key] = {
                "word": word,
                "raw_text": raw_text,
                "missing_templates": missing_templates,
                "missing_modules": missing_modules,
                "retry_count": 0
            }
            self.logger.warning(f"Definition for '{word}' has missing dependencies: "
                               f"{len(missing_templates)} templates, {len(missing_modules)} modules")
            return None
        
        # Process the definition
        try:
            processed_text = self.parser.parse(raw_text)
            self.logger.debug(f"Successfully processed definition for '{word}'")
            self.stats["success_count"] += 1
            return processed_text
        except Exception as e:
            self.logger.error(f"Error processing definition for '{word}': {str(e)}")
            self.stats["failure_count"] += 1
            return None