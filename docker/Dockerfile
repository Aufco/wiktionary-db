FROM mediawiki:1.39

# Install Lua and dependencies
RUN apt-get update && \
    apt-get install -y lua5.1 liblua5.1-0-dev git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Clone Scribunto extension
RUN cd /var/www/html/extensions && \
    git clone https://gerrit.wikimedia.org/r/mediawiki/extensions/Scribunto --branch REL1_39 && \
    chown -R www-data:www-data Scribunto

# Set working directory
WORKDIR /var/www/html