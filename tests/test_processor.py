#!/usr/bin/env python3
import sys
import os
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.database import Database
from src.wiki_processor import WikiProcessor
from src.template_manager import TemplateManager
from src.logger import setup_logger

def run_test():
    # Set up logging
    logger = setup_logger('test_processor', 'logs/test.log')
    logger.info('Starting test processor')
    
    # Sample definitions to test
    test_definitions = [
        "{{lb|en|computer science}} A [[finite]] [[string]] that is [[not]] a [[command]] or [[operator]]. {{defdate|from 20th or 21st c.}}",
        "{{n-g|Used as a [[euphemism]] for {{term|fuck|lang=en}}, {{term|fucked|lang=en}} etc.}}",
        "{{lb|en|transitive}} To [[transport]] (someone) from one place to another."
    ]
    
    # Initialize template manager
    template_manager = TemplateManager('../cache')
    
    # Initialize the wiki processor
    wiki_processor = WikiProcessor('http://localhost:8080/api.php', template_manager)
    
    # Process each test definition
    for i, raw_text in enumerate(test_definitions):
        logger.info(f"Testing definition {i+1}: {raw_text}")
        
        try:
            # Process the definition
            processed_text = wiki_processor.process_definition(raw_text)
            
            # Log the result
            logger.info(f"Result: {processed_text}")
            print(f"Test {i+1}:")
            print(f"  Raw: {raw_text}")
            print(f"  Processed: {processed_text}")
            print()
            
        except Exception as e:
            logger.error(f"Error processing test definition {i+1}: {str(e)}")
            print(f"Test {i+1} failed: {str(e)}")
    
    # Generate summary report
    template_manager.generate_summary_report()
    logger.info('Test processing complete')

if __name__ == "__main__":
    run_test()
