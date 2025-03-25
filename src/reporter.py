# src/reporter.py
def _generate_text_summary(self, path: Path, report_data: Dict):
    """Generate a human-readable text summary."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("Wiktionary Definition Processing Report\n")
        f.write("=====================================\n\n")
        f.write(f"Generated: {report_data['timestamp']}\n\n")
        
        # Processing statistics
        f.write("Processing Statistics:\n")
        f.write("-----------------------\n")
        stats = report_data["statistics"]
        f.write(f"Total definitions processed: {stats.get('processed_count', 0)}\n")
        f.write(f"Successfully processed: {stats.get('success_count', 0)}\n")
        f.write(f"Failed to process: {stats.get('failure_count', 0)}\n")
        f.write(f"Retried and succeeded: {stats.get('retry_count', 0)}\n")
        f.write(f"Still pending: {stats.get('pending_count', 0)}\n\n")
        
        # Template and module statistics
        f.write("Template and Module Statistics:\n")
        f.write("------------------------------\n")
        f.write(f"Total templates used: {len(stats.get('templates_used', []))}\n")
        f.write(f"Total modules used: {len(stats.get('modules_used', []))}\n")
        f.write(f"Templates downloaded: {len(stats.get('templates_downloaded', []))}\n")
        f.write(f"Modules downloaded: {len(stats.get('modules_downloaded', []))}\n")
        f.write(f"Templates not found: {len(stats.get('templates_missing', []))}\n")
        f.write(f"Modules not found: {len(stats.get('modules_missing', []))}\n")
        f.write(f"Download failures: {len(stats.get('download_failures', []))}\n\n")
        
        # Most common templates
        f.write("Most Common Templates:\n")
        f.write("---------------------\n")
        for template, count in stats.get('most_common_templates', [])[:20]:
            f.write(f"{template}: {count}\n")
        f.write("\n")
        
        # Most common modules
        f.write("Most Common Modules:\n")
        f.write("-------------------\n")
        for module, count in stats.get('most_common_modules', [])[:20]:
            f.write(f"{module}: {count}\n")
        f.write("\n")
        
        # Missing templates
        f.write("Missing Templates:\n")
        f.write("----------------\n")
        for template in sorted(stats.get('templates_missing', []))[:50]:
            f.write(f"{template}\n")
        if len(stats.get('templates_missing', [])) > 50:
            f.write(f"... and {len(stats.get('templates_missing', [])) - 50} more\n")
        f.write("\n")
        
        # Missing modules
        f.write("Missing Modules:\n")
        f.write("--------------\n")
        for module in sorted(stats.get('modules_missing', []))[:50]:
            f.write(f"{module}\n")
        if len(stats.get('modules_missing', [])) > 50:
            f.write(f"... and {len(stats.get('modules_missing', [])) - 50} more\n")
        f.write("\n")
        
        # Download failures
        f.write("Download Failures:\n")
        f.write("-----------------\n")
        for failure in stats.get('download_failures', [])[:50]:
            f.write(f"{failure}\n")
        if len(stats.get('download_failures', [])) > 50:
            f.write(f"... and {len(stats.get('download_failures', [])) - 50} more\n")