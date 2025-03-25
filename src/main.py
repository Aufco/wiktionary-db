# src/main.py
import argparse
import logging
import os
import sys
import time
from pathlib import Path

from .db import DatabaseManager
from .processor import DefinitionProcessor
from .downloader import TemplateDownloader
from .parser import WikitionaryParser
from .lua_engine import LuaEngine
from .reporter import Reporter

def setup_logging():
    """Set up logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "processing.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point for the Wiktionary definition processor."""
    parser = argparse.ArgumentParser(description="Process Wiktionary definitions.")
    parser.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Limit the number of definitions to process (for testing)"
    )
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset all processed_definition_text to NULL before processing"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of definitions to process in each batch"
    )
    parser.add_argument(
        "--retry-interval",
        type=int,
        default=1000,
        help="Number of definitions to process before retrying pending definitions"
    )
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Wiktionary definition processor")
    
    # Initialize components
    db_path = Path("data/wiktionary1.db")
    templates_dir = Path("templates")
    modules_dir = Path("modules")
    reports_dir = Path("reports")
    
    for directory in [templates_dir, modules_dir, reports_dir]:
        directory.mkdir(exist_ok=True)
    
    downloader = TemplateDownloader(templates_dir, modules_dir)
    lua_engine = LuaEngine(modules_dir, templates_dir)
    parser = WikitionaryParser(downloader, lua_engine)
    processor = DefinitionProcessor(downloader, parser, lua_engine)
    db_manager = DatabaseManager(db_path)
    reporter = Reporter(reports_dir)
    
    # Reset processed definitions if requested
    if args.reset:
        logger.info("Resetting all processed definitions")
        db_manager.reset_processed_definitions()
    
    # Process definitions
    logger.info(f"Processing definitions (limit: {args.limit if args.limit else 'none'})")
    total_processed = 0
    last_retry = 0
    
    try:
        while True:
            current_limit = min(args.batch_size, args.limit - total_processed if args.limit else args.batch_size)
            if current_limit <= 0:
                break
                
            definitions = db_manager.get_unprocessed_definitions(limit=current_limit)
            
            if not definitions:
                logger.info("No more unprocessed definitions")
                break
            
            for definition in definitions:
                word_id = definition["word_id"]
                word = definition["word"]
                raw_text = definition["raw_definition_text"]
                definition_id = definition["id"]
                
                processed_text = processor.process_definition(word, raw_text)
                
                if processed_text:
                    db_manager.update_processed_definition(definition_id, processed_text)
                
                total_processed += 1
                
                if total_processed % 100 == 0:
                    logger.info(f"Processed {total_processed} definitions")
                
                # Check if it's time to retry pending definitions
                if total_processed - last_retry >= args.retry_interval and processor.pending_definitions:
                    logger.info(f"Retrying pending definitions after processing {total_processed} definitions")
                    success_count, still_pending = processor.retry_pending_definitions()
                    last_retry = total_processed
                    
                    # Update the successfully processed definitions in the database
                    for def_key, def_info in list(processor.pending_definitions.items()):
                        if def_key not in processor.pending_definitions:  # It was successful
                            db_manager.update_processed_definition_by_word(
                                def_info["word"], 
                                def_info["raw_text"],
                                processor.parser.parse(def_info["raw_text"])
                            )
                
                if args.limit and total_processed >= args.limit:
                    break
            
            if args.limit and total_processed >= args.limit:
                break
        
        # Final retry for any remaining pending definitions
        if processor.pending_definitions:
            logger.info("Final retry for remaining pending definitions")
            success_count, still_pending = processor.retry_pending_definitions()
            
            # Update the successfully processed definitions in the database
            for def_key, def_info in list(processor.pending_definitions.items()):
                if def_key not in processor.pending_definitions:  # It was successful
                    db_manager.update_processed_definition_by_word(
                        def_info["word"], 
                        def_info["raw_text"],
                        processor.parser.parse(def_info["raw_text"])
                    )
        
        logger.info(f"Total definitions processed: {total_processed}")
        
        # Generate report
        logger.info("Generating report")
        processor_stats = processor.get_statistics()
        downloader_stats = downloader.get_statistics()
        reporter.generate_report({**processor_stats, **downloader_stats})
        
        logger.info("Processing completed")
    
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        
        # Generate report with current statistics
        logger.info("Generating report with current statistics")
        processor_stats = processor.get_statistics()
        downloader_stats = downloader.get_statistics()
        reporter.generate_report({
            **processor_stats, 
            **downloader_stats,
            "interrupted": True,
            "total_processed": total_processed
        })
    
    except Exception as e:
        logger.error(f"Error in main processing loop: {str(e)}")
        
        # Generate report with current statistics
        logger.info("Generating report with current statistics")
        processor_stats = processor.get_statistics()
        downloader_stats = downloader.get_statistics()
        reporter.generate_report({
            **processor_stats, 
            **downloader_stats,
            "error": str(e),
            "total_processed": total_processed
        })

if __name__ == "__main__":
    main()