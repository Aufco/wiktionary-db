import xml.etree.ElementTree as ET
import re
import os

def extract_template_names(text):
    """
    Extract template names from text containing templates.
    Handles nested templates.
    """
    template_names = set()
    
    # Use a robust approach to find templates
    i = 0
    while i < len(text):
        if text[i:i+2] == '{{':
            # Found the start of a template
            start = i + 2
            nesting = 1
            i += 2
            
            # Find the matching closing braces
            while i < len(text) and nesting > 0:
                if text[i:i+2] == '{{':
                    nesting += 1
                    i += 2
                elif text[i:i+2] == '}}':
                    nesting -= 1
                    i += 2
                else:
                    i += 1
            
            if nesting == 0:
                # We found a complete template
                template_content = text[start:i-2]
                
                # Extract the template name (before first | or entire content)
                if '|' in template_content:
                    template_name = template_content.split('|')[0].strip()
                else:
                    template_name = template_content.strip()
                
                template_names.add(template_name)
        else:
            i += 1
    
    return template_names

def process_wiktionary_dump(input_file, output_file):
    """Process the Wiktionary XML dump and extract unique template names."""
    unique_template_names = set()
    
    # Track progress
    page_count = 0
    
    # Use iterparse to process the XML file incrementally
    for event, elem in ET.iterparse(input_file, events=('end',)):
        # Only process page elements
        if elem.tag.endswith('page'):
            page_count += 1
            if page_count % 10000 == 0:
                print(f"Processed {page_count} pages, found {len(unique_template_names)} unique template names")
            
            # Find the text content of the page
            text_content = None
            for child in elem.iter():
                if child.tag.endswith('text') and child.text:
                    text_content = child.text
                    break
            
            if text_content:
                # Find all English sections (content between "{{en-" and the next "==")
                start_pos = 0
                while True:
                    # Find the next "{{en-" marker
                    en_start = text_content.find('{{en-', start_pos)
                    if en_start == -1:
                        break
                    
                    # Find the next "==" marker
                    next_header = text_content.find('==', en_start)
                    if next_header == -1:
                        # If no next header, consider the rest of the text
                        next_header = len(text_content)
                    
                    # Extract the section
                    section = text_content[en_start:next_header]
                    
                    # Extract definition lines (lines beginning with "# " or "## ")
                    lines = section.split('\n')
                    definition_lines = [line for line in lines if re.match(r'^#+\s+', line)]
                    
                    for line in definition_lines:
                        # Extract template names from the definition line
                        template_names = extract_template_names(line)
                        unique_template_names.update(template_names)
                    
                    # Move to the position after this section
                    start_pos = next_header
            
            # Clear the element to free up memory
            elem.clear()
    
    # Write the unique template names to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for template_name in sorted(unique_template_names):
            f.write(f"{template_name}\n")
    
    print(f"Completed processing {page_count} pages.")
    print(f"Found {len(unique_template_names)} unique template names.")
    print(f"Results written to {output_file}")

if __name__ == "__main__":
    input_file = r"C:\Users\benau\wiktionary-db\data\enwiktionary-latest-pages-articles.xml"
    output_file = r"C:\Users\benau\wiktionary-db\data\unique_template_names.txt"
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    process_wiktionary_dump(input_file, output_file)