# src/lua_engine.py
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

import lupa
from lupa import LuaRuntime
import requests

class LuaEngine:
    """Execute Wiktionary Lua modules within a MediaWiki-like environment."""
    
    def __init__(self, modules_dir: Path, templates_dir: Path):
        """Initialize the Lua runtime environment."""
        self.modules_dir = modules_dir
        self.templates_dir = templates_dir
        self.logger = logging.getLogger(__name__)
        
        # Ensure core modules are available
        self._ensure_core_modules()
        
        # Create Lua runtime
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        
        # Set up the MediaWiki environment
        self._setup_environment()
        
        # Cache for loaded modules
        self.loaded_modules = {}
    
    def _ensure_core_modules(self):
        """Download and set up essential core modules."""
        core_modules = [
            "ustring",
            "languages/data",
            "languages",
            "language-data",
            "Unicode/data",
            "Unicode",
            "IPA"
        ]
        
        for module in core_modules:
            module_path = self.modules_dir / f"{module.replace('/', '_')}.lua"
            
            if module_path.exists():
                continue
            
            self.logger.info(f"Downloading core module: {module}")
            
            try:
                url = f"https://en.wiktionary.org/w/api.php"
                params = {
                    "action": "query",
                    "format": "json",
                    "titles": f"Module:{module}",
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
                        self.logger.warning(f"Core module not found: {module}")
                        continue
                    
                    revisions = page_data.get("revisions", [])
                    if not revisions:
                        self.logger.warning(f"No content found for core module: {module}")
                        continue
                    
                    content = revisions[0].get("slots", {}).get("main", {}).get("*", "")
                    
                    # Create parent directories if needed
                    module_path.parent.mkdir(exist_ok=True, parents=True)
                    
                    # Save the module
                    module_path.write_text(content, encoding="utf-8")
                    
                    self.logger.info(f"Successfully downloaded core module: {module}")
            
            except Exception as e:
                self.logger.error(f"Error downloading core module {module}: {str(e)}")
    
    def _setup_environment(self):
        """Set up a MediaWiki-like Lua environment."""
        # Initialize package path to include our modules directory
        modules_path = str(self.modules_dir).replace("\\", "/")
        self.lua.execute(f"""
            package.path = package.path .. ";{modules_path}/?.lua"
            
            -- Main MediaWiki tables
            mw = {{}}
            mw.loadedModules = {{}}
            mw.loadData = function(name) return mw.loadModule(name) end
            
            -- Create frame for template processing
            mw.createFrame = function(parent, args)
                local frame = {{}}
                frame.args = args or {{}}
                frame.parent = parent
                
                frame.getParent = function()
                    return frame.parent
                end
                
                frame.getTitle = function()
                    return mw.title.getCurrentTitle()
                end
                
                frame.expandTemplate = function(self, info)
                    return mw.executeTemplate(info.title, info.args)
                end
                
                frame.callParserFunction = function(self, name, ...)
                    local args = {{...}}
                    return mw.executeParserFunction(name, args)
                end
                
                frame.preprocess = function(self, text)
                    return mw.preprocessText(text)
                end
                
                frame.newChild = function(self, args)
                    return mw.createFrame(self, args)
                end
                
                frame.extensionTag = function(self, name, content, args)
                    return content -- Simplified implementation
                end
                
                frame.argumentPairs = function(self)
                    local pairs_iter = function(t, k)
                        local v
                        k, v = next(t, k)
                        return k, v
                    end
                    return pairs_iter, frame.args, nil
                end
                
                return frame
            end
        """)
        
        # Set up the mw.* functions that Wiktionary modules use
        self._setup_mw_functions()
        
        # Register Python callbacks
        self.lua.globals().python_load_module = self._load_module_content
        self.lua.globals().python_load_template = self._load_template_content
        self.lua.globals().python_parse_wikitext = self._parse_wikitext
        self.lua.globals().python_log = self._lua_log
    
    def _setup_mw_functions(self):
        """Set up essential MediaWiki functions used by Wiktionary modules."""
        self.lua.execute("""
            -- Text processing functions
            mw.text = {}
            mw.text.trim = function(text)
                if text == nil then return nil end
                return (text:gsub("^%s*(.-)%s*$", "%1"))
            end
            
            mw.text.split = function(text, pattern, plain)
                if text == nil then return {} end
                local result = {}
                local start = 1
                local splitStart, splitEnd = string.find(text, pattern, start, plain)
                while splitStart do
                    table.insert(result, string.sub(text, start, splitStart - 1))
                    start = splitEnd + 1
                    splitStart, splitEnd = string.find(text, pattern, start, plain)
                end
                table.insert(result, string.sub(text, start))
                return result
            end
            
            mw.text.gsplit = function(text, pattern, plain)
                if text == nil then return function() return nil end end
                local start = 1
                local result = nil
                
                return function()
                    if start > string.len(text) then return nil end
                    local splitStart, splitEnd = string.find(text, pattern, start, plain)
                    if not splitStart then
                        result = string.sub(text, start)
                        start = string.len(text) + 1
                        return result
                    else
                        result = string.sub(text, start, splitStart - 1)
                        start = splitEnd + 1
                        return result
                    end
                end
            end
            
            -- Language handling
            mw.language = {}
            mw.language.getContentLanguage = function()
                return {
                    ucfirst = function(str)
                        if str == nil or str == "" then return str end
                        return string.upper(string.sub(str, 1, 1)) .. string.sub(str, 2)
                    end,
                    formatDate = function(format, timestamp)
                        return os.date(format, timestamp)
                    end,
                    convertPlural = function(count, ...)
                        local forms = {...}
                        if count == 1 then
                            return forms[1] or ""
                        else
                            return forms[2] or forms[1] or ""
                        end
                    end
                }
            end
            
            mw.language.fetchLanguageName = function(code)
                -- Simplified language name lookup
                local names = {
                    en = "English",
                    fr = "French",
                    de = "German",
                    es = "Spanish",
                    zh = "Chinese",
                    ja = "Japanese",
                    ru = "Russian",
                    -- Add more as needed or load from a data file
                }
                return names[code] or code
            end
            
            mw.language.fetchLanguageNames = function()
                -- Return a table of language codes to language names
                return {
                    ["en"] = "English",
                    ["fr"] = "French",
                    ["de"] = "German",
                    ["es"] = "Spanish",
                    ["zh"] = "Chinese",
                    ["ja"] = "Japanese",
                    ["ru"] = "Russian",
                    -- Add more as needed
                }
            end
            
            -- HTML handling
            mw.html = {}
            mw.html.create = function(tagName)
                local node = {
                    tagName = tagName,
                    attributes = {},
                    children = {},
                    
                    attr = function(self, name, value)
                        self.attributes[name] = value
                        return self
                    end,
                    
                    tag = function(self, tagName)
                        local child = mw.html.create(tagName)
                        table.insert(self.children, child)
                        return child
                    end,
                    
                    wikitext = function(self, text)
                        table.insert(self.children, {text = text})
                        return self
                    end,
                    
                    node = function(self, child)
                        table.insert(self.children, child)
                        return self
                    end,
                    
                    done = function(self)
                        if self.parents and #self.parents > 0 then
                            return self.parents[#self.parents]
                        else
                            return self
                        end
                    end,
                    
                    allDone = function(self)
                        if self.parents and #self.parents > 0 then
                            return self.parents[1]
                        else
                            return self
                        end
                    end,
                    
                    toString = function(self)
                        return self:__tostring()
                    end,
                    
                    __tostring = function(self)
                        local result = "<" .. self.tagName
                        
                        for name, value in pairs(self.attributes) do
                            result = result .. " " .. name .. "=\"" .. value .. "\""
                        end
                        
                        if #self.children == 0 then
                            result = result .. " />"
                        else
                            result = result .. ">"
                            
                            for _, child in ipairs(self.children) do
                                if type(child) == "table" then
                                    if child.text then
                                        result = result .. child.text
                                    else
                                        result = result .. tostring(child)
                                    end
                                else
                                    result = result .. tostring(child)
                                end
                            end
                            
                            result = result .. "</" .. self.tagName .. ">"
                        end
                        
                        return result
                    end
                }
                
                node.parents = {}
                return node
            end
            
            -- Title handling
            mw.title = {}
            mw.title.new = function(title, namespace)
                return {
                    fullText = title,
                    text = title,
                    prefixedText = title,
                    namespace = namespace or 0,
                    
                    getContent = function(self)
                        -- This would fetch actual content in MediaWiki
                        -- For now, we'll defer to Python for template loading
                        return python_load_template(self.text)
                    end
                }
            end
            
            mw.title.getCurrentTitle = function()
                return mw.title.new("Current")
            end
            
            -- Site information
            mw.site = {}
            mw.site.siteName = "Wiktionary"
            mw.site.namespaces = {
                [""] = 0,
                ["Talk"] = 1,
                ["User"] = 2,
                ["User_talk"] = 3,
                ["Wiktionary"] = 4,
                ["Wiktionary_talk"] = 5,
                ["File"] = 6,
                ["File_talk"] = 7,
                ["MediaWiki"] = 8,
                ["MediaWiki_talk"] = 9,
                ["Template"] = 10,
                ["Template_talk"] = 11,
                ["Help"] = 12,
                ["Help_talk"] = 13,
                ["Category"] = 14,
                ["Category_talk"] = 15,
                ["Appendix"] = 100,
                ["Appendix_talk"] = 101,
                ["Concordance"] = 102,
                ["Concordance_talk"] = 103,
                ["Index"] = 104,
                ["Index_talk"] = 105,
                ["Rhymes"] = 106,
                ["Rhymes_talk"] = 107,
                ["Transwiki"] = 108,
                ["Transwiki_talk"] = 109,
                ["Thesaurus"] = 110,
                ["Thesaurus_talk"] = 111,
                ["Citations"] = 114,
                ["Citations_talk"] = 115,
                ["Sign_gloss"] = 116,
                ["Sign_gloss_talk"] = 117,
                ["Module"] = 828,
                ["Module_talk"] = 829
            }
            
            -- Module loading
            mw.loadModule = function(name)
                if mw.loadedModules[name] then
                    return mw.loadedModules[name]
                end
                
                local content = python_load_module(name)
                if not content or content == "" then
                    error("Could not load module: " .. name)
                end
                
                -- Create environment for the module
                local env = setmetatable({}, {__index = _G})
                
                -- Load and execute the module in its environment
                local func, err = load(content, name, "t", env)
                if not func then
                    error("Error loading module " .. name .. ": " .. err)
                end
                
                local success, result = pcall(func)
                if not success then
                    error("Error executing module " .. name .. ": " .. result)
                end
                
                mw.loadedModules[name] = result
                return result
            end
            
            -- Frame variable for template execution
            frame = mw.createFrame()
            
            -- Functions for template processing
            mw.executeTemplate = function(title, args)
                local templateContent = python_load_template(title)
                if not templateContent or templateContent == "" then
                    return "{{" .. title .. "}}"
                end
                
                -- Create a new frame with the provided args
                local templateFrame = mw.createFrame(frame, args)
                
                -- In a real implementation, we would parse and execute the template
                -- For now, we'll return a placeholder
                return python_parse_wikitext(templateContent, templateFrame)
            end
            
            mw.executeParserFunction = function(name, args)
                -- Simplified parser function handling
                if name == "#invoke" then
                    if #args < 2 then
                        return "Error: #invoke requires module name and function"
                    end
                    
                    local moduleName = args[1]
                    local functionName = args[2]
                    
                    local module = mw.loadModule(moduleName)
                    if not module[functionName] then
                        return "Error: Function " .. functionName .. " not found in module " .. moduleName
                    end
                    
                    -- Remove module and function name from args
                    local functionArgs = {}
                    for i = 3, #args do
                        functionArgs[i-2] = args[i]
                    end
                    
                    -- Call the function
                    return module[functionName](unpack(functionArgs))
                end
                
                return "{{" .. name .. ":" .. table.concat(args, "|") .. "}}"
            end
            
            mw.preprocessText = function(text)
                -- In a real implementation, this would parse templates, etc.
                -- For now, we'll return the text unchanged
                return text
            end
            
            -- Message handling
            mw.message = {}
            mw.message.new = function(key, ...)
                local args = {...}
                return {
                    args = args,
                    key = key,
                    
                    plain = function(self)
                        return self.key
                    end,
                    
                    text = function(self)
                        return self.key
                    end
                }
            end
            
            -- URI handling
            mw.uri = {}
            mw.uri.new = function(uri)
                return {
                    uri = uri,
                    
                    tostring = function(self)
                        return self.uri
                    end
                }
            end
            
            -- Logging
            mw.log = function(...)
                local args = {...}
                local message = ""
                for i, arg in ipairs(args) do
                    message = message .. tostring(arg) .. "\t"
                end
                python_log(message)
            end
            
            -- Add basic utility library
            mw.ustring = require('ustring')
            
            -- Add utility functions for template handling
            mw.getCurrentFrame = function()
                return frame
            end
            
            mw.addWarning = function(text)
                return text
            end
        """)
    
    def _load_module_content(self, module_name: str) -> str:
        """Load a module's content from the filesystem (called from Lua)."""
        try:
            # Clean up module name
            clean_name = module_name.replace("Module:", "").replace("/", "_").replace(":", "_")
            module_path = self.modules_dir / f"{clean_name}.lua"
            
            if module_path.exists():
                return module_path.read_text(encoding="utf-8")
            
            self.logger.warning(f"Module not found: {module_name} (looked for {module_path})")
            return ""
        except Exception as e:
            self.logger.error(f"Error loading module {module_name}: {str(e)}")
            return ""
    
    def _load_template_content(self, template_name: str) -> str:
        """Load a template's content from the filesystem (called from Lua)."""
        try:
            # Clean up template name
            clean_name = template_name.replace("Template:", "").replace("/", "_").replace(":", "_")
            template_path = self.templates_dir / f"{clean_name}.txt"
            
            if template_path.exists():
                return template_path.read_text(encoding="utf-8")
            
            self.logger.warning(f"Template not found: {template_name} (looked for {template_path})")
            return ""
        except Exception as e:
            self.logger.error(f"Error loading template {template_name}: {str(e)}")
            return ""
    
    def _parse_wikitext(self, wikitext: str, frame) -> str:
        """Parse wikitext with template substitution (called from Lua)."""
        # This is a simplified implementation
        # In a real implementation, we would handle template substitution
        return wikitext
    
    def _lua_log(self, message: str):
        """Log a message from Lua."""
        self.logger.debug(f"Lua: {message}")
    
    def invoke_module(self, module_name: str, function_name: str, args=None) -> str:
        """Invoke a Lua module function."""
        try:
            # Clean up module name
            module_name = module_name.replace("Module:", "")
            
            # Create arguments table
            if args is None:
                args = {}
            
            # Convert Python dict to Lua table
            lua_args = self.lua.table()
            for k, v in args.items():
                lua_args[k] = v
            
            # Create frame with arguments
            frame = self.lua.globals().mw.createFrame(None, lua_args)
            
            # Load module
            module = self.lua.globals().mw.loadModule(module_name)
            
            # Call function
            if function_name in module:
                result = module[function_name](frame)
                return str(result) if result is not None else ""
            else:
                self.logger.error(f"Function {function_name} not found in module {module_name}")
                return f"[[Error: Function {function_name} not found in module {module_name}]]"
        
        except Exception as e:
            self.logger.error(f"Error invoking module {module_name}.{function_name}: {str(e)}")
            return f"[[Error: {str(e)}]]"
    
    def expand_template(self, template_name: str, args=None) -> str:
        """Expand a template with given arguments."""
        try:
            # Convert Python dict to Lua table
            if args is None:
                args = {}
            
            lua_args = self.lua.table()
            for k, v in args.items():
                lua_args[k] = v
            
            # Call template expansion function
            result = self.lua.globals().mw.executeTemplate(template_name, lua_args)
            return str(result) if result is not None else ""
        
        except Exception as e:
            self.logger.error(f"Error expanding template {template_name}: {str(e)}")
            return f"[[Error: {str(e)}]]"
    
    def process_wikitext(self, wikitext: str) -> str:
        """Process wikitext using the Lua environment."""
        try:
            # Process template invocations using regex
            def replace_template(match):
                template_text = match.group(0)
                template_content = match.group(1)
                
                if not template_content:
                    return template_text
                
                parts = template_content.split("|")
                if not parts:
                    return template_text
                
                template_name = parts[0].strip()
                
                # Handle parser functions like #invoke
                if template_name.startswith("#"):
                    if template_name == "#invoke":
                        if len(parts) < 3:
                            return template_text
                        
                        module_name = parts[1].strip()
                        function_name = parts[2].strip()
                        
                        # Extract arguments
                        args = {}
                        for i, arg in enumerate(parts[3:], 1):
                            # Check for named arguments (name=value)
                            if "=" in arg:
                                name, value = arg.split("=", 1)
                                args[name.strip()] = value.strip()
                            else:
                                args[i] = arg.strip()
                        
                        # Invoke module
                        return self.invoke_module(module_name, function_name, args)
                    else:
                        # Handle other parser functions
                        return template_text
                
                # Regular template
                # Extract arguments
                args = {}
                for i, arg in enumerate(parts[1:], 1):
                    # Check for named arguments (name=value)
                    if "=" in arg:
                        name, value = arg.split("=", 1)
                        args[name.strip()] = value.strip()
                    else:
                        args[i] = arg.strip()
                
                # Expand template
                return self.expand_template(template_name, args)
            
            # Process templates
            import re
            processed_text = re.sub(r'\{\{(.*?)\}\}', replace_template, wikitext)
            
            # Process wikilinks [[link]] and [[link|text]]
            processed_text = re.sub(r'\[\[([^|]+?)(?:\|([^\]]+?))?\]\]', 
                                    lambda m: m.group(2) if m.group(2) else m.group(1), 
                                    processed_text)
            
            return processed_text
        
        except Exception as e:
            self.logger.error(f"Error processing wikitext: {str(e)}")
            return wikitext