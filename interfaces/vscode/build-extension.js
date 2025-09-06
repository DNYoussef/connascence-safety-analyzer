#!/usr/bin/env node

/**
 * Build script for VS Code extension with fallback support
 * Handles corrupted source files by using pre-compiled outputs
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Building Connascence VS Code Extension...\n');

// Check if we have compiled files
const outDir = path.join(__dirname, 'out');
const extensionJS = path.join(outDir, 'extension.js');

if (fs.existsSync(extensionJS)) {
    console.log('✅ Found compiled extension.js, proceeding with packaging...');
    
    try {
        // Create .vsix package
        console.log('📦 Creating .vsix package...');
        execSync('vsce package --no-dependencies --allow-missing-repository --baseContentUrl https://github.com/connascence-systems/vscode-extension', { stdio: 'inherit' });
        
        // Find the created .vsix file
        const files = fs.readdirSync(__dirname);
        const vsixFile = files.find(f => f.endsWith('.vsix'));
        
        if (vsixFile) {
            console.log(`\n✅ Extension packaged successfully: ${vsixFile}`);
            
            // Get file info
            const stats = fs.statSync(path.join(__dirname, vsixFile));
            console.log(`📊 Package size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
            console.log(`📅 Created: ${stats.mtime.toLocaleString()}`);
            
            return vsixFile;
        } else {
            throw new Error('No .vsix file found after packaging');
        }
        
    } catch (error) {
        console.error('❌ Packaging failed:', error.message);
        
        // Fallback: Try with basic config
        console.log('🔄 Attempting fallback packaging...');
        
        // Update package.json to use simple-extension.js if available
        const simpleExtensionJS = path.join(outDir, 'simple-extension.js');
        if (fs.existsSync(simpleExtensionJS)) {
            const packagePath = path.join(__dirname, 'package.json');
            const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
            pkg.main = './out/simple-extension.js';
            fs.writeFileSync(packagePath, JSON.stringify(pkg, null, 2));
            
            try {
                execSync('vsce package --no-dependencies --allow-missing-repository --baseContentUrl https://github.com/connascence-systems/vscode-extension', { stdio: 'inherit' });
                
                const files = fs.readdirSync(__dirname);
                const vsixFile = files.find(f => f.endsWith('.vsix'));
                
                if (vsixFile) {
                    console.log(`\n✅ Fallback packaging successful: ${vsixFile}`);
                    return vsixFile;
                }
            } catch (fallbackError) {
                console.error('❌ Fallback packaging also failed:', fallbackError.message);
                throw fallbackError;
            }
        }
    }
} else {
    console.error('❌ No compiled extension found. Cannot package.');
    console.log('💡 Try running: npm run compile');
    process.exit(1);
}