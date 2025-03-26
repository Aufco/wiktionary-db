<?php
# MediaWiki Local Settings
wfLoadExtension( 'Scribunto' );
$wgScribuntoDefaultEngine = 'luastandalone';
$wgScribuntoEngineConf['luastandalone']['luaPath'] = '/usr/bin/lua5.1';

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