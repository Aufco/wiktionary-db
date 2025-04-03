FROM mediawiki:1.39

# Install Lua and dependencies with proper error handling
RUN apt-get update && \
    apt-get install -y lua5.1 liblua5.1-0-dev git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Clone Scribunto extension properly
RUN cd /var/www/html/extensions && \
    git clone https://gerrit.wikimedia.org/r/mediawiki/extensions/Scribunto --branch REL1_39 && \
    cd Scribunto && \
    if [ -f "setupScrunto.php" ]; then php setupScrunto.php lua standalone; fi && \
    chown -R www-data:www-data /var/www/html/extensions/Scribunto

# Set working directory
WORKDIR /var/www/html