#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Build configuration
const config = {
  environment: process.env.NODE_ENV || 'production',
  version: process.env.npm_package_version || '1.0.0',
  buildTime: new Date().toISOString(),
  gitHash: getGitHash(),
};

function getGitHash() {
  try {
    return execSync('git rev-parse --short HEAD', { encoding: 'utf8' }).trim();
  } catch {
    return 'unknown';
  }
}

function createBuildInfo() {
  const buildInfo = {
    version: config.version,
    buildTime: config.buildTime,
    gitHash: config.gitHash,
    environment: config.environment,
    nodeVersion: process.version,
    platform: process.platform,
    arch: process.arch,
  };

  const buildInfoPath = path.join(__dirname, '../dist/build-info.json');
  fs.writeFileSync(buildInfoPath, JSON.stringify(buildInfo, null, 2));
  console.log('✅ Build info created:', buildInfoPath);
}

function analyzeBundle() {
  try {
    console.log('📊 Analyzing bundle size...');
    execSync('npx vite-bundle-analyzer dist', { stdio: 'inherit' });
  } catch (error) {
    console.log('⚠️ Bundle analyzer not available, skipping analysis');
  }
}

function validateBuild() {
  const distPath = path.join(__dirname, '../dist');
  
  if (!fs.existsSync(distPath)) {
    throw new Error('❌ Build directory not found');
  }

  const requiredFiles = ['index.html', 'assets'];
  for (const file of requiredFiles) {
    const filePath = path.join(distPath, file);
    if (!fs.existsSync(filePath)) {
      throw new Error(`❌ Required file not found: ${file}`);
    }
  }

  console.log('✅ Build validation passed');
}

function optimizeAssets() {
  const distPath = path.join(__dirname, '../dist');
  
  // Compress HTML
  try {
    const htmlPath = path.join(distPath, 'index.html');
    let html = fs.readFileSync(htmlPath, 'utf8');
    
    // Remove comments and extra whitespace
    html = html
      .replace(/<!--[\s\S]*?-->/g, '')
      .replace(/\s+/g, ' ')
      .trim();
    
    fs.writeFileSync(htmlPath, html);
    console.log('✅ HTML optimized');
  } catch (error) {
    console.log('⚠️ HTML optimization failed:', error.message);
  }

  // Create robots.txt
  const robotsContent = `User-agent: *
Allow: /

Sitemap: /sitemap.xml`;
  fs.writeFileSync(path.join(distPath, 'robots.txt'), robotsContent);
  console.log('✅ robots.txt created');

  // Create sitemap.xml
  const sitemapContent = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>/</loc>
    <lastmod>${config.buildTime}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>`;
  fs.writeFileSync(path.join(distPath, 'sitemap.xml'), sitemapContent);
  console.log('✅ sitemap.xml created');
}

function main() {
  console.log('🚀 Starting build process...');
  console.log(`📦 Environment: ${config.environment}`);
  console.log(`🏷️ Version: ${config.version}`);
  console.log(`⏰ Build time: ${config.buildTime}`);
  console.log(`🔗 Git hash: ${config.gitHash}`);

  try {
    // Run Vite build
    console.log('🔨 Running Vite build...');
    execSync(`npm run build`, { stdio: 'inherit' });

    // Create build info
    createBuildInfo();

    // Validate build
    validateBuild();

    // Optimize assets
    optimizeAssets();

    // Analyze bundle (optional)
    if (process.argv.includes('--analyze')) {
      analyzeBundle();
    }

    console.log('🎉 Build completed successfully!');
    console.log(`📁 Output directory: ${path.join(__dirname, '../dist')}`);
    
  } catch (error) {
    console.error('❌ Build failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { config, createBuildInfo, validateBuild, optimizeAssets };
