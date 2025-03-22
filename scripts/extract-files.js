const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const dataDir = path.join(__dirname, '..', 'data');
const bzFile = path.join(dataDir, 'enwiktionary-latest-pages-articles.xml.bz2');
const gzFile = path.join(dataDir, 'enwiktionary-latest-langlinks.sql.gz');
const xmlFile = path.join(dataDir, 'enwiktionary-latest-pages-articles.xml');
const sqlFile = path.join(dataDir, 'enwiktionary-latest-langlinks.sql');

// Extract BZ2 file
function extractBZ2() {
  console.log('Extracting BZ2 file...');
  
  // Use PowerShell and 7-Zip to extract (assuming 7-Zip is installed)
  const result = spawnSync('powershell', [
    '-Command',
    `& {
      $7zPath = "C:\\Program Files\\7-Zip\\7z.exe"
      if (Test-Path $7zPath) {
        & $7zPath e "${bzFile}" -o"${dataDir}" -y
        Write-Host "Extraction complete"
      } else {
        Write-Host "7-Zip not found. Please install 7-Zip or extract the file manually."
      }
    }`
  ], { stdio: 'inherit' });
  
  if (result.error) {
    console.error('Error extracting BZ2 file:', result.error);
    console.log('Please extract the file manually');
  }
}

// Extract GZ file
function extractGZ() {
  console.log('Extracting GZ file...');
  
  // Use PowerShell and 7-Zip to extract (assuming 7-Zip is installed)
  const result = spawnSync('powershell', [
    '-Command',
    `& {
      $7zPath = "C:\\Program Files\\7-Zip\\7z.exe"
      if (Test-Path $7zPath) {
        & $7zPath e "${gzFile}" -o"${dataDir}" -y
        Write-Host "Extraction complete"
      } else {
        Write-Host "7-Zip not found. Please install 7-Zip or extract the file manually."
      }
    }`
  ], { stdio: 'inherit' });
  
  if (result.error) {
    console.error('Error extracting GZ file:', result.error);
    console.log('Please extract the file manually');
  }
}

// Check if files need extraction
if (!fs.existsSync(xmlFile) && fs.existsSync(bzFile)) {
  extractBZ2();
} else {
  console.log('XML file already exists or BZ2 file not found');
}

if (!fs.existsSync(sqlFile) && fs.existsSync(gzFile)) {
  extractGZ();
} else {
  console.log('SQL file already exists or GZ file not found');
}

console.log('Extraction process completed');