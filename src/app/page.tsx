'use client';

import { useState, useEffect } from 'react';

interface Definition {
  id: number;
  definition: string;
  example: string | null;
}

interface PartOfSpeech {
  type: string;
  definitions: Definition[];
}

interface WordData {
  word: string;
  language: string;
  partsOfSpeech: PartOfSpeech[];
}

interface Language {
  id: number;
  code: string;
  name: string;
  word_count: number;
}

export default function Home() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const [wordData, setWordData] = useState<WordData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  // Fetch languages when the component mounts
  useEffect(() => {
    async function fetchLanguages() {
      try {
        const response = await fetch('/api/search', { method: 'OPTIONS' });
        const data = await response.json();
        if (data.languages) {
          setLanguages(data.languages);
        }
      } catch (error) {
        console.error('Error fetching languages:', error);
      }
    }

    fetchLanguages();
    
    // Load recent searches from localStorage
    const savedSearches = localStorage.getItem('recentSearches');
    if (savedSearches) {
      setRecentSearches(JSON.parse(savedSearches));
    }
  }, []);

  // Function to search for a word
  const searchWord = async (word: string, language: string) => {
    if (!word.trim()) {
      setError('Please enter a word to search');
      return;
    }

    setLoading(true);
    setError(null);
    setWordData(null);

    try {
      const response = await fetch(`/api/search?word=${encodeURIComponent(word)}&language=${encodeURIComponent(language)}`);
      const data = await response.json();

      if (response.ok) {
        setWordData(data);
        
        // Save to recent searches
        const updatedSearches = [word, ...recentSearches.filter(s => s !== word)].slice(0, 10);
        setRecentSearches(updatedSearches);
        localStorage.setItem('recentSearches', JSON.stringify(updatedSearches));
      } else {
        setError(data.error || 'No results found');
      }
    } catch (error) {
      setError('An error occurred while searching');
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    searchWord(searchTerm, selectedLanguage);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Wiktionary Database</h1>
          <p className="text-gray-600 dark:text-gray-300">Search for word definitions from Wiktionary</p>
        </header>

        <div className="max-w-3xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
          <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Search for a word
              </label>
              <input
                type="text"
                id="search"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Enter a word..."
              />
            </div>
            
            <div className="md:w-1/3">
              <label htmlFor="language" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Language
              </label>
              <select
                id="language"
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                {languages.map((lang) => (
                  <option key={lang.id} value={lang.name}>
                    {lang.name} ({lang.word_count > 0 ? lang.word_count : 'No'} words)
                  </option>
                ))}
              </select>
            </div>
            
            <button
              type="submit"
              className="mt-auto md:self-end px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md shadow transition-colors duration-200"
            >
              Search
            </button>
          </form>

          {/* Recent searches */}
          {recentSearches.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">Recent searches:</p>
              <div className="flex flex-wrap gap-2 mt-1">
                {recentSearches.map((search, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setSearchTerm(search);
                      searchWord(search, selectedLanguage);
                    }}
                    className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-full transition-colors duration-200"
                  >
                    {search}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {loading && (
          <div className="text-center py-8">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-2 text-gray-600 dark:text-gray-300">Searching...</p>
          </div>
        )}

        {error && (
          <div className="max-w-3xl mx-auto bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-8">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {wordData && (
          <div className="max-w-3xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{wordData.word}</h2>
              <p className="text-gray-600 dark:text-gray-300">{wordData.language}</p>
            </div>
            
            <div className="p-6">
              {wordData.partsOfSpeech.map((pos, posIndex) => (
                <div key={posIndex} className="mb-6 last:mb-0">
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">
                    {pos.type}
                  </h3>
                  
                  <ol className="list-decimal list-inside space-y-2">
                    {pos.definitions.map((def, defIndex) => (
                      <li key={defIndex} className="text-gray-700 dark:text-gray-300">
                        <span>{def.definition}</span>
                        
                        {def.example && (
                          <p className="ml-6 mt-1 text-sm italic text-gray-600 dark:text-gray-400">
                            Example: {def.example}
                          </p>
                        )}
                      </li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}