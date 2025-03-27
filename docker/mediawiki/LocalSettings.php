<?php
# Database settings
$wgDBtype = "mysql";
$wgDBserver = "db";
$wgDBname = "wiki_db";
$wgDBuser = "wikiuser";
$wgDBpassword = "wikipass";

# Site settings
$wgSitename = "Wiktionary Processor";
$wgScriptPath = "";
$wgServer = "http://localhost:8080";

# Allow API access
$wgEnableAPI = true;
$wgEnableWriteAPI = true;
$wgCrossSiteAJAXdomains = ['*'];

# Set up namespaces for templates and modules
$wgExtraNamespaces[10] = 'Template';
$wgExtraNamespaces[828] = 'Module';

# Configure for Wiktionary-like processing
$wgNamespacesWithSubpages[NS_MAIN] = true;
$wgAllowExternalImages = true;

# Increase limits for processing complex templates
$wgMaxArticleSize = 10485760; # 10MB
$wgMaxPPNodeCount = 1000000;
$wgMaxTemplateDepth = 100;
$wgMaxPPExpandDepth = 100;

# Scribunto settings
wfLoadExtension('Scribunto');
$wgScribuntoDefaultEngine = 'luastandalone';
$wgScribuntoEngineConf['luastandalone']['luaPath'] = '/usr/bin/lua5.1';

# Debugging
$wgShowExceptionDetails = true;
$wgShowDBErrorBacktrace = true;
$wgDebugLogFile = "/var/www/html/debug.log";

# Required at the end
$wgUpgradeKey = "abc123";