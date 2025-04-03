import os
import re
import html
import sqlite3
import time
from datetime import datetime

# Set paths for input file and output database
input_file = r"C:\Users\benau\wiktionary-db\data\enwiktionary-latest-pages-articles.xml"
output_dir = os.path.dirname(os.path.abspath(__file__))
output_db = os.path.join(output_dir, "wiktionary.db")
max_words = 0  # Set to 0 for unlimited processing
log_file = os.path.join(output_dir, "parser_log.txt")

# Create a fresh log file
with open(log_file, "w", encoding="utf-8") as f:
    f.write("Wiktionary Parser Log - First 20 Pages\n")
    f.write("=====================================\n\n")
    f.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

def log_message(message):
    """Log a message to the log file"""
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")

def create_database():
    """Create SQLite database with the required schema and performance optimizations"""
    try:
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        
        # Performance optimizations
        cursor.execute('PRAGMA page_size = 4096;')
        cursor.execute('PRAGMA cache_size = 10000;')
        cursor.execute('PRAGMA journal_mode = WAL;')
        cursor.execute('PRAGMA synchronous = NORMAL;')
        
        # Create words table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL UNIQUE,
            total_senses INTEGER NOT NULL
        )
        ''')
        
        # Create definitions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS definitions (
            id INTEGER PRIMARY KEY,
            word_id INTEGER NOT NULL,
            part_of_speech TEXT NOT NULL,
            definition_text TEXT NOT NULL,
            sense_number INTEGER NOT NULL,
            FOREIGN KEY (word_id) REFERENCES words(id)
        )
        ''')
        
        # Create index on word for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_word ON words(word)
        ''')
        
        # Create index on word_id and sense_number for faster pagination
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_word_sense ON definitions(word_id, sense_number)
        ''')
        
        conn.commit()
        log_message("Database created successfully")
        return conn
    except Exception as e:
        log_message(f"Error creating database: {str(e)}")
        return None

def pre_process_nested_templates(text):
    """Pre-process text to handle complex nested templates."""
    try:
        # First, process {{m}} templates within other templates
        iteration = 0
        max_iterations = 5  # Limit iterations to prevent infinite loops
        
        while '{{m|' in text and iteration < max_iterations:
            # Find all {{m}} templates
            m_pattern = r'\{\{m\|([^|}]+)\|([^|}]+)(?:\|[^}]+)?\}\}'
            m_matches = list(re.finditer(m_pattern, text))
            
            if not m_matches:
                break
                
            # Replace each {{m}} template with just the word
            for m_match in reversed(m_matches):  # Process in reverse to avoid index issues
                lang = m_match.group(1)
                word = m_match.group(2)
                text = text[:m_match.start()] + word + text[m_match.end():]
            
            iteration += 1
        
        return text
    except Exception:
        return text  # Return original text on error

def strip_references(text):
    """Remove reference tags and their content."""
    try:
        # Remove <ref>...</ref> tags and their content, handling HTML entities
        text = re.sub(r'&lt;ref&gt;.*?&lt;/ref&gt;', '', text)
        # Also handle actual <ref> tags (not just entity-encoded ones)
        text = re.sub(r'<ref[^>]*>.*?</ref>', '', text)
        return text
    except Exception:
        return text

def strip_date_templates(text):
    """Remove date templates that indicate when a word came into use."""
    try:
        # Remove {{defdate|...}} templates
        text = re.sub(r'\{\{defdate\|[^}]+\}\}', '', text)
        return text
    except Exception:
        return text

def strip_maintenance_templates(text):
    """Remove maintenance and editorial templates."""
    try:
        # Remove request templates (rfv-sense, rfd-sense, rfclarify, rfdef, etc.)
        text = re.sub(r'\{\{rf[^}]+\}\}', '', text)
        
        # Remove metadata templates like senseid
        text = re.sub(r'\{\{senseid\|[^}]+\}\}', '', text)
        text = re.sub(r'\{\{translation only[^}]*\}\}', '', text)
        
        # Remove literal translation sense marker
        text = re.sub(r'\{\{\&lit[^}]*\}\}', '', text)
        
        # Remove uncertain definition templates
        text = re.sub(r'\{\{def-uncertain[^}]*\}\}', '', text)
        text = re.sub(r'\{\{descendant only[^}]*\}\}', '', text)
        
        # Remove ISBN templates
        text = re.sub(r'\{\{ISBN\|[^}]+\}\}', '', text)
        
        return text
    except Exception:
        return text

def transform_context_labels(text):
    """Transform context and usage label templates."""
    try:
        # Handle context label templates (lb, label, context, cx)
        def context_label_replacement(match):
            try:
                params = match.group(1).split('|')
                # Skip the language code (usually the first parameter after template name)
                if len(params) > 1:
                    # Filter out parameters that are metadata (lang=, etc.)
                    labels = []
                    for param in params[1:]:
                        param = param.strip()
                        # Skip parameters with equals sign (metadata like lang=en)
                        if not re.match(r'^[a-z]+=', param):
                            # Handle underscores as separators, not labels
                            if param == '_':
                                continue  # Skip underscores
                            labels.append(param)
                    
                    if labels:
                        # Join labels with commas, but handle "outside certain phrases" type labels specially
                        joined_labels = []
                        i = 0
                        while i < len(labels):
                            # Check if this label is followed by "outside certain phrases" or similar
                            if i < len(labels) - 1 and labels[i+1].startswith("outside"):
                                joined_labels.append(f"{labels[i]} {labels[i+1]}")
                                i += 2
                            else:
                                joined_labels.append(labels[i])
                                i += 1
                        
                        return f"({', '.join(joined_labels)}) "
                return ""
            except Exception:
                return ""
        
        text = re.sub(r'\{\{(?:lb|label|context|cx)\|([^}]+)\}\}', context_label_replacement, text)
        
        # Handle dedicated grammatical labels
        grammatical_labels = ["transitive", "intransitive", "countable", "uncountable"]
        for label in grammatical_labels:
            text = re.sub(r'\{\{' + label + r'[^}]*\}\}', f"({label}) ", text)
        
        # Handle qualifiers
        text = re.sub(r'\{\{(?:qualifier|qual|q)\|([^}]+)\}\}', r'(\1) ', text)
        
        # Handle non-gloss definitions
        text = re.sub(r'\{\{non-gloss(?: definition)?\|([^}]+)\}\}', r'\1', text)
        
        return text
    except Exception:
        return text

def transform_taxonomic_templates(text):
    """Transform taxonomic formatting templates."""
    try:
        # Handle taxfmt template
        text = re.sub(r'\{\{taxfmt\|([^|}]+)(?:\|[^}]+)?\}\}', r'\1', text)
        
        # Handle taxlink template
        text = re.sub(r'\{\{taxlink\|([^|}]+)(?:\|[^}]+)?\}\}', r'\1', text)
        
        # Handle taxon template
        text = re.sub(r'\{\{taxon\|([^|}]+)(?:\|[^}]+)?\}\}', r'\1', text)
        
        # Handle specieslink template
        text = re.sub(r'\{\{specieslink\|([^|}]+)(?:\|[^}]+)?\}\}', r'\1', text)
        
        return text
    except Exception:
        return text

def transform_latin_definition_templates(text):
    """Handle Latn-def templates for Latin script letter definitions."""
    try:
        def latn_def_replacement(match):
            try:
                params = match.group(1).split('|')
                if len(params) < 4:
                    return "A letter of the alphabet."
                
                lang = params[0]  # Language code (e.g., 'en')
                type_param = params[1]  # 'letter' or 'ordinal'
                number = params[2]  # Position/number (e.g., '1', '2')
                letter = params[3]  # The letter itself
                
                # Convert number to ordinal text
                ordinal_map = {
                    '1': 'first', '2': 'second', '3': 'third', '4': 'fourth', '5': 'fifth',
                    '6': 'sixth', '7': 'seventh', '8': 'eighth', '9': 'ninth', '10': 'tenth',
                    '11': 'eleventh', '12': 'twelfth', '13': 'thirteenth', '14': 'fourteenth',
                    '15': 'fifteenth', '16': 'sixteenth', '17': 'seventeenth', '18': 'eighteenth',
                    '19': 'nineteenth', '20': 'twentieth', '21': 'twenty-first', '22': 'twenty-second',
                    '23': 'twenty-third', '24': 'twenty-fourth', '25': 'twenty-fifth', '26': 'twenty-sixth'
                }
                
                ordinal = ordinal_map.get(number, str(number) + 'th')
                
                # Language mapping
                lang_name = {'en': 'English', 'fr': 'French', 'de': 'German', 'es': 'Spanish', 
                             'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch'}.get(lang, 'the')
                
                if type_param == 'letter':
                    return f"The {ordinal} letter of the {lang_name} alphabet, called {letter} and written in the Latin script."
                elif type_param == 'ordinal':
                    return f"The ordinal number {ordinal}, derived from this letter of the {lang_name} alphabet, called {letter} and written in the Latin script."
                else:
                    return f"A {type_param} based on the letter {letter} in the Latin script."
            except Exception:
                return "A letter of the alphabet."
        
        text = re.sub(r'\{\{Latn-def\|([^}]+)\}\}', latn_def_replacement, text)
        return text
    except Exception:
        return text

def extract_form_of_parameters(params, with_lang_code=True):
    """
    Extract parameters from form-of templates more robustly.
    
    Args:
        params (list): List of parameter strings
        with_lang_code (bool): Whether the first parameter is a language code
    
    Returns:
        tuple: (term, display_text)
    """
    try:
        term = ""  # Initialize with empty string instead of None
        display_text = ""  # Initialize with empty string
        
        # Skip language code if needed
        start_idx = 1 if with_lang_code and len(params) > 1 and re.match(r'^[a-z]{2,3}$', params[0]) else 0
        
        # Look for term (first non-metadata parameter)
        for i in range(start_idx, len(params)):
            if i < len(params):  # Additional safety check
                param = params[i].strip()
                if param.startswith('t='):
                    display_text = param[2:] if param[2:] else ""
                elif param.startswith('tr=') or param.startswith('id=') or param.startswith('nodot='):
                    continue  # Skip these metadata parameters
                elif not term and not re.match(r'^[a-z]+=', param):
                    # This is the main term (lemma)
                    term = param if param else ""
        
        # Ensure we don't return None for either value
        return term or "", display_text or ""
    except Exception:
        return "", ""  # Return empty strings on error

def transform_form_of_templates(text):
    """Transform form-of templates to readable phrases."""
    try:
        # Handle "ellipsis of" template
        def ellipsis_of_replacement(match):
            try:
                content = match.group(1) if match.group(1) else ""
                
                # First handle wikilinks
                content = re.sub(r'\[\[([^|\]]+)(?:\|([^]]+))?\]\]', 
                                lambda m: (m.group(2) if m.group(2) else m.group(1)) if m.group(1) else "", 
                                content)
                
                params = content.split('|')
                if len(params) < 2:
                    return "Ellipsis"
                
                # Get language code (should be first parameter)
                lang_code = params[0]
                
                # Second parameter should be the term
                term = params[1] if len(params) > 1 else ""
                
                if term:
                    return f"Ellipsis of {term}"
                
                return "Ellipsis"
            except Exception:
                return "Ellipsis"
        
        # Process ellipsis of template
        text = re.sub(r'\{\{ellipsis of\|([^}]+)\}\}', ellipsis_of_replacement, text)
        
        # Handle "alt form" template which is an abbreviation for "alternative form of"
        def alt_form_replacement(match):
            try:
                content = match.group(1) if match.group(1) else ""
                
                # First handle wikilinks
                content = re.sub(r'\[\[([^|\]]+)(?:\|([^]]+))?\]\]', 
                                lambda m: (m.group(2) if m.group(2) else m.group(1)) if m.group(1) else "", 
                                content)
                
                parts = content.split('|')
                if len(parts) < 2:
                    return "Alternative form"
                
                # Get language code (should be first parameter)
                lang_code = parts[0]
                
                # Second parameter should be the term (e.g., "pi")
                term = parts[1] if len(parts) > 1 else ""
                
                # Look for definition in subsequent parameters
                # In this template, empty parameters are sometimes used as separators
                definition = ""
                for i in range(2, len(parts)):
                    if parts[i].strip():  # Skip empty parameters
                        definition = parts[i].strip()
                        break
                
                if term:
                    if definition:
                        return f"Alternative form of {term} (\"{definition}\")"
                    else:
                        return f"Alternative form of {term}"
                
                return "Alternative form"
            except Exception:
                return "Alternative form"
        
        # Process alt form template
        text = re.sub(r'\{\{alt form\|([^}]+)\}\}', alt_form_replacement, text)
        
        # Handle form-of templates with careful parameter extraction
        def form_of_replacement(match):
            try:
                template_name = match.group(1).lower() if match.group(1) else ""
                content = match.group(2) if match.group(2) else ""
                
                # First handle special cases for wikilinks inside templates
                # Replace [[word]] with word and [[word|display]] with display
                content = re.sub(r'\[\[([^|\]]+)(?:\|([^]]+))?\]\]', 
                                lambda m: (m.group(2) if m.group(2) else m.group(1)) if m.group(1) else "", 
                                content)
                
                params = content.split('|')
                if not params:
                    return template_name or ""
                
                # Extract term and display text
                term, display_text = extract_form_of_parameters(params)
                
                # Now term is guaranteed to be at least an empty string
                if not term:
                    return template_name or ""
                    
                # Format the output
                if display_text:
                    return f"{template_name} {term} (\"{display_text}\")"
                else:
                    return f"{template_name} {term}"
            except Exception:
                return ""
        
        # List of form-of templates to process
        form_of_templates = [
            'alternative spelling of', 'alternative form of', 
            'obsolete spelling of', 'archaic spelling of',
            'short for', 'abbreviation of', 'plural of', 'singular of',
            'past of', 'present participle of', 'past participle of',
            'comparative of', 'superlative of', 'misspelling of',
            'contraction of', 'romanization of', 'combining form of',
            'eye dialect of', 'obsolete form of', 'archaic form of',
            'dated form of', 'dated spelling of', 'diminutive of',
            'augmentative of', 'feminine of', 'masculine of', 'gerund of',
            'imperative of', 'infinitive of', 'conjugation of', 'form of',
            'initialism of', 'acronym of', 'clipping of', 'synonym of',
            'euphemism for'
        ]
        
        # Process templates
        for template_name in form_of_templates:
            template_name_escaped = re.escape(template_name)
            pattern = r'\{\{(' + template_name_escaped + r')\|([^}]+)\}\}'
            text = re.sub(pattern, form_of_replacement, text)
        
        # Handle alt sp template (alternative spelling)
        def alt_sp_replacement(match):
            try:
                content = match.group(1) if match.group(1) else ""
                
                # First handle wikilinks
                content = re.sub(r'\[\[([^|\]]+)(?:\|([^]]+))?\]\]', 
                                lambda m: (m.group(2) if m.group(2) else m.group(1)) if m.group(1) else "", 
                                content)
                
                params = content.split('|')
                if len(params) < 2:
                    return "Alternative spelling"
                
                # Extract term and display text
                term, display_text = extract_form_of_parameters(params)
                
                # Now term is guaranteed to be at least an empty string
                if not term:
                    return "Alternative spelling"
                    
                # Format the output
                if display_text:
                    return f"Alternative spelling of {term} (\"{display_text}\")"
                else:
                    return f"Alternative spelling of {term}"
            except Exception:
                return "Alternative spelling"
        
        # Process alt sp template
        text = re.sub(r'\{\{alt sp\|([^}]+)\}\}', alt_sp_replacement, text)
        
        # Handle inflection template
        def inflection_replacement(match):
            try:
                content = match.group(1) if match.group(1) else ""
                
                # Handle wikilinks
                content = re.sub(r'\[\[([^|\]]+)(?:\|([^]]+))?\]\]', 
                                lambda m: (m.group(2) if m.group(2) else m.group(1)) if m.group(1) else "", 
                                content)
                
                parts = content.split('|')
                
                if len(parts) < 2:
                    return "Form of"  # Fallback
                
                term, _ = extract_form_of_parameters(parts)
                
                if not term:
                    return "Form of"
                    
                attributes = []
                
                # Extract relevant attributes and ignore metadata
                for part in parts[1:]:
                    if part and not re.match(r'^[a-z]+=', part):
                        if part != term:  # Avoid duplicating the term in the attributes
                            attributes.append(part)
                
                if attributes:
                    # Format as "first-person singular present indicative of lemma"
                    return f"{'-'.join(attributes)} of {term}"
                else:
                    return f"form of {term}"
            except Exception:
                return "Form of"
        
        # Apply the inflection template handler
        text = re.sub(r'\{\{inflection of\|([^}]+)\}\}', inflection_replacement, text)
        
        return text
    except Exception:
        return text

def transform_name_templates(text):
    """Transform name and proper noun templates."""
    try:
        # Handle given name template
        def given_name_replacement(match):
            try:
                content = match.group(1) if match.group(1) else ""
                parts = content.split('|')
                gender = "given name"
                origin = ""
                
                for part in parts[1:]:  # Skip language code
                    if part in ["male", "female", "unisex"]:
                        gender = f"{part} given name"
                    elif part.startswith("from="):
                        origin = f" from {part[5:]}"
                
                return f"A {gender}{origin}"
            except Exception:
                return "A given name"
        
        text = re.sub(r'\{\{given name\|([^}]+)\}\}', given_name_replacement, text)
        
        # Handle surname template
        def surname_replacement(match):
            try:
                content = match.group(1) if match.group(1) else ""
                parts = content.split('|')
                origin = ""
                
                for part in parts[1:]:
                    if part.startswith("from="):
                        origin = f" from {part[5:]}"
                
                return f"A surname{origin}"
            except Exception:
                return "A surname"
        
        text = re.sub(r'\{\{surname\|([^}]+)\}\}', surname_replacement, text)
        
        # Handle place name template
        def place_replacement(match):
            try:
                content = match.group(1) if match.group(1) else ""
                parts = content.split('|')
                if len(parts) < 3:
                    return "A place"
                    
                place_type = parts[1]
                locations = []
                
                for part in parts[2:]:
                    if part.startswith(("p/", "s/", "c/")):
                        locations.append(part[2:])
                
                if locations:
                    return f"A {place_type} in {', '.join(locations)}"
                return f"A {place_type}"
            except Exception:
                return "A place"
        
        text = re.sub(r'\{\{place\|([^}]+)\}\}', place_replacement, text)
        
        # Handle demonym templates
        text = re.sub(r'\{\{demonym-noun\|[^|}]+\|([^}|]+)(?:\|[^}]+)?\}\}', 
                      lambda m: f"A native or inhabitant of {m.group(1)}" if m.group(1) else "A native or inhabitant", 
                      text)
        text = re.sub(r'\{\{demonym-adj\|[^|}]+\|([^}|]+)(?:\|[^}]+)?\}\}', 
                      lambda m: f"Of or relating to {m.group(1)}" if m.group(1) else "Of or relating to", 
                      text)
        
        # Handle other name templates
        text = re.sub(r'\{\{city nickname\|[^|}]+\|([^}|]+)(?:\|[^}]+)?\}\}', 
                      lambda m: f"A nickname for {m.group(1)}" if m.group(1) else "A nickname", 
                      text)
        
        return text
    except Exception:
        return text

def transform_usage_templates(text):
    """Transform usage and example templates."""
    try:
        # Handle affix usage examples
        def affix_usage_replacement(match):
            try:
                template = match.group(1) if match.group(1) else ""
                content = match.group(2) if match.group(2) else ""
                parts = content.split('|')
                if len(parts) < 3:
                    return ""
                    
                if template == "prefixusex":
                    return f"{parts[1]}- + {parts[2]} → {parts[1]}{parts[2]}"
                elif template == "suffixusex":
                    return f"{parts[1]} + -{parts[2]} → {parts[1]}{parts[2]}"
                else:  # affixusex
                    return f"{parts[1]} + {parts[2]} → {parts[1]}{parts[2]}"
            except Exception:
                return ""
        
        text = re.sub(r'\{\{(affixusex|prefixusex|suffixusex)\|([^}]+)\}\}', affix_usage_replacement, text)
        
        # Handle "used in" templates
        text = re.sub(r'\{\{only used in\|([^}]+)\}\}', lambda m: f"Only used in {m.group(1)}" if m.group(1) else "Only used in specific context", text)
        
        def used_in_phrasal_verbs_replacement(match):
            try:
                content = match.group(1) if match.group(1) else ""
                verbs = content.split('|')
                if verbs:
                    return f"Used in phrasal verbs such as {', '.join(verbs)}"
                return ""
            except Exception:
                return ""
        
        text = re.sub(r'\{\{used in phrasal verbs\|([^}]+)\}\}', used_in_phrasal_verbs_replacement, text)
        
        # Handle construed template
        text = re.sub(r'\{\{construed with\|([^}]+)\}\}', lambda m: f"(construed with \"{m.group(1)}\")" if m.group(1) else "", text)
        
        # Handle inline examples (mostly strip)
        text = re.sub(r'\{\{(?:collocation|coa|quotei)\|[^|}]+\|([^}]+)\}\}', '', text)
        
        return text
    except Exception:
        return text

def transform_inline_links(text):
    """Transform inline links to plain text."""
    try:
        # Handle wikilinks with display text
        def wikilink_replacement(match):
            try:
                link = match.group(1) if match.group(1) else ""
                display = match.group(2)
                return display if display else link
            except Exception:
                return ""
        
        text = re.sub(r'\[\[([^|\]]+)(?:\|([^]]+))?\]\]', wikilink_replacement, text)
        
        # Handle external/Wikipedia links
        def wikipedia_link_replacement(match):
            try:
                link = match.group(1) if match.group(1) else ""
                display = match.group(2)
                return display if display else link
            except Exception:
                return ""
        
        text = re.sub(r'\{\{w(?:torw)?\|([^}|]+)(?:\|([^}]+))?\}\}', wikipedia_link_replacement, text)
        
        # Handle link templates - {{l|en|word}}
        def l_template_replacement(match):
            try:
                content = match.group(1) if match.group(1) else ""
                parts = content.split('|')
                
                # Need at least a language code and a term
                if len(parts) < 2:
                    return ""
                    
                # The term should be the second parameter (after language code)
                return parts[1]
            except Exception:
                return ""
        
        text = re.sub(r'\{\{l\|([^}]+)\}\}', l_template_replacement, text)
        
        # Handle m-templates that might have been missed by preprocessing
        text = re.sub(r'\{\{m\|([^|}]+)\|([^|}]+)(?:\|[^}]+)?\}\}', lambda m: m.group(2) if m.group(2) else "", text)
        
        # Handle URLs
        text = re.sub(r'\[https?://[^ ]+ ([^]]+)\]', lambda m: m.group(1) if m.group(1) else "", text)
        text = re.sub(r'\[https?://[^] ]+\]', '', text)
        
        return text
    except Exception:
        return text

def transform_formatting(text):
    """Transform formatting markup to plain text."""
    try:
        # Handle italic or bold formatting
        text = re.sub(r"'''([^']+)'''", r'\1', text)  # Bold
        text = re.sub(r"''([^']+)''", r'\1', text)  # Italic
        
        # Handle HTML entities by decoding them
        try:
            text = html.unescape(text)
        except Exception:
            pass
        
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        return text
    except Exception:
        return text

def clean_remaining_templates(text):
    """
    Clean up any remaining templates not handled by specific functions.
    Handles nested templates by working from innermost to outermost.
    """
    try:
        # Find and remove templates from innermost to outermost
        iteration = 0
        max_iterations = 10  # Prevent infinite loops
        
        while '{{' in text and '}}' in text and iteration < max_iterations:
            # Simple template pattern - may not catch all nested cases but will work iteratively
            match = re.search(r'\{\{[^{}]*\}\}', text)
            if match:
                # Check if it's a template we want to preserve part of
                template = match.group(0)
                if '|' in template:
                    # Extract the content of the template (assuming format {{name|content}})
                    parts = template[2:-2].split('|')
                    if len(parts) > 1:
                        # Replace with just the content, skipping the template name
                        replacement = parts[1] if not parts[1].startswith(('lang=', 't=', 'tr=')) else ''
                        text = text[:match.start()] + replacement + text[match.end():]
                    else:
                        text = text[:match.start()] + text[match.end():]
                else:
                    text = text[:match.start()] + text[match.end():]
            else:
                # If no simple templates found but {{ and }} still exist,
                # we might have a complex nested structure - try a more aggressive approach
                text = re.sub(r'\{\{[^}]*\}\}', '', text)
                # Break to avoid infinite loop in pathological cases
                break
            iteration += 1
        
        # Cleanup any stray {{ or }} that might remain
        text = text.replace('{{', '').replace('}}', '')
        
        return text
    except Exception:
        return text

def clean_whitespace(text):
    """Clean up whitespace and normalize punctuation."""
    try:
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove space before punctuation
        text = re.sub(r' ([.,;:!?])', r'\1', text)
        
        # Ensure there's a space after punctuation if followed by a letter
        text = re.sub(r'([.,;:!?])([a-zA-Z])', r'\1 \2', text)
        
        # Remove extra spaces around 'or' and 'and'
        text = re.sub(r' (or|and) ', r' \1 ', text)
        
        # Ensure proper spacing for parenthesized content
        text = re.sub(r'\( ', r'(', text)
        text = re.sub(r' \)', r')', text)
        
        # Fix capitalization at the beginning
        def fix_capitalization(match):
            try:
                word = match.group(2) if match.group(2) else ""
                # Keep these words lowercase even at the start of a sentence
                if word.lower() in ['alternative', 'short', 'plural', 'singular', 'obsolete', 
                                   'abbreviation', 'initialism', 'acronym', 'clipping',
                                   'contraction', 'diminutive', 'feminine', 'masculine',
                                   'ellipsis']:
                    return (match.group(1) if match.group(1) else "") + word.lower()
                return (match.group(1) if match.group(1) else "") + word
            except Exception:
                return match.group(0) if match and match.group(0) else ""
        
        text = re.sub(r'^(\([^)]+\) )?([\w]+)', fix_capitalization, text)
        
        # Normalize punctuation around or/and
        text = re.sub(r' or\s+', ' or ', text)
        text = re.sub(r' and\s+', ' and ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    except Exception:
        return text

def parse_wiktionary_definition(definition_text):
    """
    Process a Wiktionary definition line to clean up markup and return plain text.
    
    Args:
        definition_text (str): Raw Wiktionary definition text starting with "# "
        
    Returns:
        str: Cleaned definition text
    """
    try:
        # Remove the leading "# " if present
        if definition_text.startswith("# "):
            definition_text = definition_text[2:]
        elif definition_text.startswith("## "):
            definition_text = definition_text[3:]
        
        # Pre-process to handle known nested templates
        definition_text = pre_process_nested_templates(definition_text)
        
        # Remove reference tags first
        definition_text = strip_references(definition_text)
        
        # Process templates and markup iteratively until no more changes are made
        # This helps with nested templates
        prev_text = ""
        current_text = definition_text
        iteration = 0
        max_iterations = 10  # Prevent infinite loops
        
        while prev_text != current_text and iteration < max_iterations:
            prev_text = current_text
            
            # Apply transformation functions in order
            current_text = strip_maintenance_templates(current_text)
            current_text = strip_date_templates(current_text)  # Remove date templates
            current_text = transform_context_labels(current_text)
            current_text = transform_taxonomic_templates(current_text)
            current_text = transform_latin_definition_templates(current_text)
            current_text = transform_form_of_templates(current_text)
            current_text = transform_name_templates(current_text)
            current_text = transform_usage_templates(current_text)
            current_text = transform_inline_links(current_text)
            current_text = transform_formatting(current_text)
            current_text = clean_remaining_templates(current_text)
            
            iteration += 1
        
        # Final cleanup
        current_text = clean_whitespace(current_text)
        
        # Add final period if needed
        if current_text and not current_text.endswith(('.', '!', '?')):
            current_text += '.'
        
        return current_text
    except Exception:
        return "Definition parsing error."  # Fallback definition

def extract_and_clean_definitions(xml_text, word=""):
    """
    Extract definitions from XML text and clean them.
    
    Args:
        xml_text (str): XML content for a Wiktionary page
        word (str): The word being processed
        
    Returns:
        list: List of tuples (part_of_speech, definition_text)
    """
    try:
        entries = []
        blocks = list(re.finditer(r"\{\{en-([a-z]+)[^}]*\}\}(.*?)(?=\n==|\Z)", xml_text, re.DOTALL))

        for block in blocks:
            part_of_speech = block.group(1).capitalize()
            block_text = block.group(2)

            for line in block_text.splitlines():
                # Process both main definitions "# " and sub-definitions "## "
                if line.startswith("# ") or line.startswith("## "):
                    # Skip lines that end with a colon (category headers)
                    if line.rstrip().endswith(":"):
                        continue
                        
                    try:
                        # Apply our parsing logic to clean the definition
                        cleaned_definition = parse_wiktionary_definition(line)
                        if cleaned_definition:  # Only add non-empty definitions
                            entries.append((part_of_speech, cleaned_definition))
                    except Exception:
                        # Skip errors silently
                        pass

        return entries
    except Exception:
        return []

def process_large_dump_file():
    """
    Process the Wiktionary XML dump file and store definitions in a SQLite database.
    No limit on number of words processed, but logs the first 20.
    """
    # Create/connect to the database
    conn = create_database()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            page_buffer = []
            inside_page = False
            processed_words = 0
            logged_words = 0
            start_time = time.time()
            
            for line in file:
                if "<page>" in line:
                    inside_page = True
                    page_buffer = [line]
                elif "</page>" in line and inside_page:
                    page_buffer.append(line)
                    inside_page = False
                    full_page = "".join(page_buffer)

                    title_match = re.search(r"<title>(.*?)</title>", full_page)
                    if not title_match:
                        continue
                    
                    word = title_match.group(1).strip()
                    
                    try:
                        # Extract and clean definitions
                        definition_entries = extract_and_clean_definitions(full_page, word)
                        
                        if definition_entries:
                            # Insert the word into the words table
                            total_senses = len(definition_entries)
                            cursor.execute(
                                "INSERT OR IGNORE INTO words (word, total_senses) VALUES (?, ?)",
                                (word, total_senses)
                            )
                            
                            # Get the word_id (either newly inserted or pre-existing)
                            cursor.execute("SELECT id FROM words WHERE word = ?", (word,))
                            word_id = cursor.fetchone()[0]
                            
                            # Insert each definition
                            for i, (part_of_speech, definition_text) in enumerate(definition_entries, 1):
                                cursor.execute(
                                    "INSERT INTO definitions (word_id, part_of_speech, definition_text, sense_number) VALUES (?, ?, ?, ?)",
                                    (word_id, part_of_speech, definition_text, i)
                                )
                            
                            # Only log the first 20 words
                            if logged_words < 20:
                                log_message(f"\nWord {logged_words+1}: {word}")
                                log_message(f"Total senses: {total_senses}")
                                
                                # Log each definition
                                for i, (part_of_speech, definition_text) in enumerate(definition_entries, 1):
                                    log_message(f"  {i}. {part_of_speech} - {definition_text}")
                                
                                logged_words += 1
                                
                                if logged_words == 20:
                                    log_message("\nReached 20 logged words. Continuing processing without logging...")
                            
                            processed_words += 1
                            
                            # Commit every 1000 words
                            if processed_words % 1000 == 0:
                                conn.commit()
                                
                    except Exception:
                        # Silently ignore errors for individual words
                        pass
                elif inside_page:
                    page_buffer.append(line)
            
            # Final commit
            conn.commit()
            
            # Log final stats
            elapsed = time.time() - start_time
            log_message(f"\nProcessing complete.")
            log_message(f"Total words processed: {processed_words}")
            log_message(f"Total time: {elapsed:.2f} seconds")
            if elapsed > 0:
                log_message(f"Processing rate: {processed_words / elapsed:.2f} words/second")
            log_message(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
    except Exception as e:
        log_message(f"Error processing file: {str(e)}")
    
    finally:
        # Close the database connection
        if conn:
            conn.close()

def main():
    """Main function to run the script"""
    start_time = time.time()
    log_message(f"Starting Wiktionary parser, output will be stored in {output_db}")
    log_message(f"Processing file: {input_file}")
    
    process_large_dump_file()
    
    elapsed = time.time() - start_time
    log_message(f"Total script execution time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    main()