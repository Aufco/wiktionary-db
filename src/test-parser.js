import { parseWikitext } from './parsers/wikitext-parser.js';

// Sample wikitext content for testing
const testWikitext = `==English==

===Etymology===
From {{inh|en|enm|free}}.

===Pronunciation===
* {{enPR|frē}}, {{IPA|en|/fɹiː/}}
* {{audio|en|En-uk-free.ogg|a=UK}}
* {{homophones|en|three|aa=th-fronting}}

===Adjective===
{{en-adj|er|more}}

# {{lb|en|social}} [[unconstrained|Unconstrained]].
#: {{syn|en|unconstrained|unfettered|unhindered|quit}}
#: {{ant|en|constrained|restricted}}
#: {{ux|en|He was given '''free''' rein to do whatever he wanted.}}
# Obtainable without any [[payment]].
#: {{syn|en|free of charge|gratis|costless|feeless}}
#: {{ux|en|The government provides '''free''' health care.}}

===Verb===
{{en-verb}}

# {{lb|en|transitive}} To [[release]].
# {{lb|en|transitive}} To [[make]] available.

==French==

===Pronunciation===
* {{fr-IPA}}

===Adjective===
{{fr-adj}}

# [[cool|Cool]].
`;

// Test function
function testParser() {
  console.log('Testing wikitext parser...');
  
  try {
    const entries = parseWikitext('free', testWikitext);
    
    console.log('Parsed entries:', JSON.stringify(entries, null, 2));
    console.log(`Found ${entries.length} language entries`);
    
    for (const entry of entries) {
      console.log(`\nLanguage: ${entry.language.name} (${entry.language.code})`);
      
      for (const section of entry.sections) {
        console.log(`\n  Part of Speech: ${section.pos}`);
        console.log(`  Etymology Number: ${section.etymologyNumber}`);
        
        for (let i = 0; i < section.definitions.length; i++) {
          const def = section.definitions[i];
          console.log(`\n    Definition ${i+1}: ${def.text}`);
          
          if (def.examples.length > 0) {
            console.log('    Examples:');
            for (const example of def.examples) {
              console.log(`      - ${example}`);
            }
          }
        }
      }
    }
    
    console.log('\nTest completed successfully!');
  } catch (error) {
    console.error('Test failed:', error);
  }
}

testParser();