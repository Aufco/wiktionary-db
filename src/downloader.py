# src/downloader.py - updated download_module method

def download_module(self, module_name: str) -> bool:
    """Download a module from Wiktionary."""
    # Clean up module name
    clean_name = module_name.replace("Module:", "")
    
    if clean_name in self.available_modules:
        return True
    
    self.logger.info(f"Downloading module: {clean_name}")
    
    try:
        url = f"https://en.wiktionary.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": f"Module:{clean_name}",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main"
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Extract content from the response
        pages = data.get("query", {}).get("pages", {})
        
        for page_id, page_data in pages.items():
            if page_id == "-1":  # Page doesn't exist
                self.logger.warning(f"Module not found: {clean_name}")
                self.stats["modules_missing"].add(clean_name)
                return False
            
            revisions = page_data.get("revisions", [])
            if not revisions:
                self.logger.warning(f"No content found for module: {clean_name}")
                self.stats["modules_missing"].add(clean_name)
                return False
            
            content = revisions[0].get("slots", {}).get("main", {}).get("*", "")
            
            # Save the module
            module_path = self.modules_dir / f"{clean_name}.lua"
            module_path.write_text(content, encoding="utf-8")
            
            self.available_modules.add(clean_name)
            self.stats["modules_downloaded"].add(clean_name)
            self.logger.info(f"Successfully downloaded module: {clean_name}")
            
            # Check for module dependencies
            self._check_module_dependencies(content)
            
            return True
        
        return False
    
    except Exception as e:
        self.logger.error(f"Error downloading module {clean_name}: {str(e)}")
        self.stats["download_failures"].append(f"Module:{clean_name} - {str(e)}")
        return False

def _check_module_dependencies(self, content: str) -> None:
    """Extract and download module dependencies."""
    # Look for require statements and mw.loadData calls
    dependency_patterns = [
        r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        r'mw\.loadData\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        r'mw\.loadModule\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
    ]
    
    dependencies = set()
    for pattern in dependency_patterns:
        for match in re.findall(pattern, content):
            # Clean up module name
            if match.startswith("Module:"):
                match = match[7:]
            dependencies.add(match)
    
    # Download dependencies
    for dependency in dependencies:
        if dependency not in self.available_modules:
            self.download_module(dependency)