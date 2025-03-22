# Define variables
$dataFolder = "C:\Users\benau\wiktionary-db\data"
$baseUrl = "https://dumps.wikimedia.org/enwiktionary/latest"
$files = @(
    "enwiktionary-latest-pages-articles.xml.bz2",
    "enwiktionary-latest-langlinks.sql.gz"
)

# Create data folder if it doesn't exist
if (-not (Test-Path $dataFolder)) {
    New-Item -Path $dataFolder -ItemType Directory
}

# Download each file
foreach ($file in $files) {
    $url = "$baseUrl/$file"
    $output = Join-Path $dataFolder $file
    
    Write-Host "Downloading $file..."
    Invoke-WebRequest -Uri $url -OutFile $output
    Write-Host "Downloaded $file to $output"
}

Write-Host "All files downloaded successfully!"