#!/usr/bin/env python3
import argparse
import logging
import sys
import os
from database import Database
from wiki_processor import WikiProcessor
from template_manager import TemplateManager
from logger import setup_logger

def main():
    parser = argparse.ArgumentParser(description='Wiktionary Definition Processor')
    parser.add_argument('--test', action='store_true', help='Run in test mode with limited processing')
    parser.add_argument('--limit', type=int, default=100, help='Limit number of entries to process in test mode')
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logger('wiktionary_processor', 'logs/processing.log')
    logger.info('Starting Wiktionary Definition Processor')
    
    # Connect to the database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'wiktionary1.db')
    db = Database(db_path)
    logger.info(f'Connected to database: {db_path}')
    
    # Initialize the template manager
    template_manager = TemplateManager('cache')
    
    # Initialize the wiki processor
    wiki_processor = WikiProcessor('http://localhost:8080/api.php', template_manager)
    
    # Reset all processed definition text to NULL
    db.reset_processed_definitions()
    logger.info('Reset all processed definition text fields to NULL')
    
    # Process definitions
    process_definitions(db, wiki_processor, logger, test_mode=args.test, limit=args.limit)
    
    logger.info('Processing complete')

def process_definitions(db, wiki_processor, logger, test_mode=False, limit=100):
    """Process all definitions in the database"""
    total_definitions = db.get_total_definitions_count()
    logger.info(f'Found {total_definitions} definitions to process')
    
    if test_mode:
        logger.info(f'Running in test mode. Processing only {limit} definitions')
        definitions = db.get_definitions(limit=limit)
    else:
        definitions = db.get_definitions()
    
    processed_count = 0
    error_count = 0
    
    for definition in definitions:
        definition_id, word_id, raw_text = definition
        logger.debug(f'Processing definition ID {definition_id}')
        
        try:
            # Process the definition
            processed_text = wiki_processor.process_definition(raw_text)
            
            # Store the processed result
            db.update_processed_definition(definition_id, processed_text)
            
            processed_count += 1
            if processed_count % 100 == 0:
                logger.info(f'Processed {processed_count}/{total_definitions} definitions')
                
        except Exception as e:
            logger.error(f'Error processing definition ID {definition_id}: {str(e)}')
            error_count += 1
    
    logger.info(f'Processing complete. Processed {processed_count} definitions. Errors: {error_count}')
    # Generate summary report
    wiki_processor.template_manager.generate_summary_report()

if __name__ == "__main__":
    main()