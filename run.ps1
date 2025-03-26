# Wiktionary Definition Processor Launcher
# Usage: .\run.ps1 [--test] [--limit N]

param(
    [switch]$test,
    [int]$limit = 100
)

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
cd $scriptPath

function Ensure-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "Docker is not installed or not in PATH. Please install Docker Desktop." -ForegroundColor Red
        exit 1
    }
    Write-Host "Docker is installed." -ForegroundColor Green
}

function Ensure-Python {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "Python is not installed or not in PATH. Please install Python 3.8+." -ForegroundColor Red
        exit 1
    }
    
    $pythonVersion = python --version
    Write-Host "Python is installed: $pythonVersion" -ForegroundColor Green
    
    # Ensure required packages
    Write-Host "Installing required Python packages..." -ForegroundColor Yellow
    python -m pip install requests
}

function Ensure-Directories {
    # Create required directories
    New-Item -Path "logs" -ItemType Directory -Force | Out-Null
    New-Item -Path "cache" -ItemType Directory -Force | Out-Null
    New-Item -Path "cache/Template" -ItemType Directory -Force | Out-Null
    New-Item -Path "cache/Module" -ItemType Directory -Force | Out-Null
    Write-Host "Directory structure created." -ForegroundColor Green
}

function Start-DockerEnvironment {
    Write-Host "Starting Docker containers for MediaWiki environment..." -ForegroundColor Yellow
    cd docker
    docker-compose up -d
    cd ..
    
    # Wait for MediaWiki to be ready
    Write-Host "Waiting for MediaWiki to initialize (this may take a minute)..." -ForegroundColor Yellow
    $attempts = 0
    $maxAttempts = 30
    $ready = $false
    
    while (-not $ready -and $attempts -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8080/api.php" -Method Head -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                $ready = $true
                Write-Host "MediaWiki is ready!" -ForegroundColor Green
            }
        } catch {
            $attempts++
            Write-Host "Waiting for MediaWiki to be ready... ($attempts/$maxAttempts)" -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        }
    }
    
    if (-not $ready) {
        Write-Host "MediaWiki failed to initialize within the expected time. Please check Docker logs." -ForegroundColor Red
        exit 1
    }
}

function Start-Processing {
    Write-Host "Starting definition processing..." -ForegroundColor Green
    
    $args = @()
    if ($test) {
        $args += "--test"
    }
    if ($limit -ne 100) {
        $args += "--limit"
        $args += $limit.ToString()
    }
    
    python src/main.py $args
}

# Main execution
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Wiktionary Definition Processor" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

Ensure-Docker
Ensure-Python
Ensure-Directories
Start-DockerEnvironment
Start-Processing

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Processing complete!" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
