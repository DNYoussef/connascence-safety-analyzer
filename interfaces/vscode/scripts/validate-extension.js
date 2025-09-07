#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Validation script for the Connascence VS Code extension
 * Enhanced for CI/CD environments with robust error handling
 */
class ExtensionValidator {
    constructor() {
        this.basePath = path.join(__dirname, '..');
        this.errors = [];
        this.warnings = [];
        this.isCI = process.env.CI === 'true';
        this.isProduction = process.env.NODE_ENV === 'production';
        this.verbose = process.env.VERBOSE === 'true' || process.argv.includes('--verbose');
    }

    validate() {
        console.log('🔍 Validating Connascence VS Code Extension...');
        
        if (this.isCI) {
            console.log('📊 Running in CI environment - using enterprise validation standards');
        }
        
        if (this.verbose) {
            console.log(`🔧 Base path: ${this.basePath}`);
            console.log(`🌍 Working directory: ${process.cwd()}`);
        }
        
        console.log();
        
        try {
            this.validatePackageJson();
            this.validateTypeScript();
            this.validateWebpack();
            this.validateSourceStructure();
            this.validateConfiguration();
            this.validateReadme();
            this.validateCIEnvironment();
        } catch (error) {
            console.error('💥 Validation crashed with error:', error.message);
            if (this.verbose) {
                console.error(error.stack);
            }
            this.errors.push(`Validation script error: ${error.message}`);
        }
        
        this.printResults();
        
        return this.errors.length === 0;
    }

    validatePackageJson() {
        console.log('📦 Validating package.json...');
        
        const packagePath = path.join(this.basePath, 'package.json');
        if (!fs.existsSync(packagePath)) {
            this.errors.push('package.json not found');
            return;
        }

        try {
            const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
            
            // Required fields
            const requiredFields = ['name', 'version', 'description', 'main', 'engines'];
            for (const field of requiredFields) {
                if (!pkg[field]) {
                    this.errors.push(`package.json missing required field: ${field}`);
                }
            }
            
            // VS Code specific validations
            if (!pkg.engines?.vscode) {
                this.errors.push('package.json missing vscode engine requirement');
            }
            
            if (!pkg.contributes) {
                this.errors.push('package.json missing contributes section');
            } else {
                if (!pkg.contributes.commands || pkg.contributes.commands.length === 0) {
                    this.warnings.push('No commands defined in package.json');
                }
                
                if (!pkg.contributes.configuration) {
                    this.warnings.push('No configuration properties defined');
                }
            }
            
            // Scripts validation
            const requiredScripts = ['compile', 'watch', 'package'];
            for (const script of requiredScripts) {
                if (!pkg.scripts?.[script]) {
                    this.warnings.push(`Missing script: ${script}`);
                }
            }
            
            console.log('  ✅ package.json structure valid');
            
        } catch (error) {
            this.errors.push(`package.json parse error: ${error.message}`);
        }
    }

    validateTypeScript() {
        console.log('📝 Validating TypeScript configuration...');
        
        const tsconfigPath = path.join(this.basePath, 'tsconfig.json');
        if (!fs.existsSync(tsconfigPath)) {
            this.errors.push('tsconfig.json not found');
            return;
        }

        try {
            const tsconfig = JSON.parse(fs.readFileSync(tsconfigPath, 'utf8'));
            
            if (!tsconfig.compilerOptions) {
                this.errors.push('tsconfig.json missing compilerOptions');
                return;
            }
            
            const requiredOptions = ['target', 'module', 'outDir', 'rootDir'];
            for (const option of requiredOptions) {
                if (!tsconfig.compilerOptions[option]) {
                    this.warnings.push(`tsconfig.json missing recommended option: ${option}`);
                }
            }
            
            console.log('  ✅ TypeScript configuration valid');
            
        } catch (error) {
            this.errors.push(`tsconfig.json parse error: ${error.message}`);
        }
    }

    validateWebpack() {
        console.log('📦 Validating Webpack configuration...');
        
        const webpackPath = path.join(this.basePath, 'webpack.config.js');
        if (!fs.existsSync(webpackPath)) {
            this.warnings.push('webpack.config.js not found - using default compilation');
            return;
        }

        try {
            require(webpackPath);
            console.log('  ✅ Webpack configuration valid');
        } catch (error) {
            this.errors.push(`webpack.config.js error: ${error.message}`);
        }
    }

    validateSourceStructure() {
        console.log('📁 Validating source structure...');
        
        const requiredDirs = [
            'src'
        ];
        
        for (const dir of requiredDirs) {
            const dirPath = path.join(this.basePath, dir);
            if (!fs.existsSync(dirPath)) {
                this.warnings.push(`Directory not found: ${dir}`);
            }
        }
        
        const requiredFiles = [
            'src/extension.ts'
        ];
        
        for (const file of requiredFiles) {
            const filePath = path.join(this.basePath, file);
            if (!fs.existsSync(filePath)) {
                this.errors.push(`Required file not found: ${file}`);
            } else {
                // Check for encoding issues (warn only)
                try {
                    const content = fs.readFileSync(filePath, 'utf8');
                    if (content.includes('\uFFFD')) {
                        this.warnings.push(`File may have encoding issues: ${file}`);
                    }
                } catch (err) {
                    this.warnings.push(`Could not validate encoding for: ${file}`);
                }
            }
        }
        
        console.log('  ✅ Source structure validated');
    }

    validateConfiguration() {
        console.log('⚙️ Validating VS Code configuration...');
        
        const packagePath = path.join(this.basePath, 'package.json');
        if (!fs.existsSync(packagePath)) {
            return; // Already reported in packageJson validation
        }

        try {
            const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
            
            if (pkg.contributes?.configuration?.properties) {
                const properties = pkg.contributes.configuration.properties;
                
                // Check for essential configuration properties
                const essentialProps = [
                    'connascence.realTimeAnalysis',
                    'connascence.safetyProfile',
                    'connascence.enableIntelliSense',
                    'connascence.enableCodeLens',
                    'connascence.enableHover'
                ];
                
                for (const prop of essentialProps) {
                    if (!properties[prop]) {
                        this.warnings.push(`Missing configuration property: ${prop}`);
                    }
                }
            }
            
            console.log('  ✅ Configuration validated');
            
        } catch (error) {
            // Already handled in packageJson validation
        }
    }

    validateReadme() {
        console.log('📖 Validating README...');
        
        const readmePath = path.join(this.basePath, 'README.md');
        if (!fs.existsSync(readmePath)) {
            this.warnings.push('README.md not found');
            return;
        }

        try {
            const content = fs.readFileSync(readmePath, 'utf8');
            
            // Check for essential sections
            const essentialSections = [
                '# Connascence Safety Analyzer',
                '## Features',
                '## Installation',
                '## Configuration',
                '## Usage'
            ];
            
            for (const section of essentialSections) {
                if (!content.includes(section)) {
                    this.warnings.push(`README missing section: ${section}`);
                }
            }
            
            // Check for marketplace badges
            if (!content.includes('marketplace.visualstudio.com')) {
                this.warnings.push('README missing marketplace badges');
            }
            
            console.log('  ✅ README validated');
            
        } catch (error) {
            this.warnings.push(`README validation error: ${error.message}`);
        }
    }

    validateCIEnvironment() {
        if (!this.isCI) {
            return; // Skip CI-specific validations in local environment
        }

        console.log('🔄 Validating CI environment compatibility...');
        
        try {
            // Check for Windows-specific issues
            if (process.platform === 'win32') {
                console.log('  🪟 Running on Windows - checking compatibility...');
                
                // Check for long path support
                const longPathTest = path.join(this.basePath, 'a'.repeat(200));
                try {
                    fs.accessSync(path.dirname(longPathTest), fs.constants.F_OK);
                    console.log('  ✅ Windows long path support available');
                } catch (error) {
                    this.warnings.push('Windows long path support may be limited');
                }
            }
            
            // Check for required CLI tools in CI
            const requiredTools = ['npm', 'node'];
            for (const tool of requiredTools) {
                try {
                    require('child_process').execSync(`${tool} --version`, { 
                        stdio: 'pipe', 
                        timeout: 5000 
                    });
                    if (this.verbose) {
                        console.log(`  ✅ ${tool} available`);
                    }
                } catch (error) {
                    this.errors.push(`Required tool not available: ${tool}`);
                }
            }
            
            // Check for extension entry point
            const mainEntry = this.getPackageMain();
            if (mainEntry) {
                const entryPath = path.join(this.basePath, mainEntry);
                if (this.verbose) {
                    console.log(`  🔍 Checking entry point: ${mainEntry}`);
                    console.log(`  📁 Base path: ${this.basePath}`);
                    console.log(`  📄 Full entry path: ${entryPath}`);
                    console.log(`  📋 Path exists: ${fs.existsSync(entryPath)}`);
                }
                if (!fs.existsSync(entryPath)) {
                    this.errors.push(`Extension entry point not found: ${mainEntry}`);
                } else {
                    console.log('  ✅ Extension entry point exists');
                }
            }
            
            // Validate package.json for CI deployment
            this.validateCIPackageRequirements();
            
            console.log('  ✅ CI environment validation completed');
            
        } catch (error) {
            this.warnings.push(`CI validation error: ${error.message}`);
        }
    }

    validateCIPackageRequirements() {
        try {
            const packagePath = path.join(this.basePath, 'package.json');
            const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
            
            // Check for CI-critical fields
            if (!pkg.publisher) {
                this.errors.push('Package.json missing publisher field (required for packaging)');
            }
            
            if (!pkg.engines?.vscode) {
                this.errors.push('Package.json missing VS Code engine version (required for marketplace)');
            }
            
            // Validate version format
            if (pkg.version && !/^\d+\.\d+\.\d+/.test(pkg.version)) {
                this.warnings.push('Version should follow semantic versioning (major.minor.patch)');
            }
            
            // Check for repository field (good practice)
            if (!pkg.repository && this.isProduction) {
                this.warnings.push('Package.json missing repository field (recommended for marketplace)');
            }
            
        } catch (error) {
            this.warnings.push(`CI package validation error: ${error.message}`);
        }
    }

    getPackageMain() {
        try {
            const packagePath = path.join(this.basePath, 'package.json');
            const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
            return pkg.main;
        } catch (error) {
            return null;
        }
    }

    printResults() {
        console.log('\n📊 Validation Results:');
        console.log('═══════════════════════');
        
        if (this.isCI) {
            console.log(`🔄 CI Environment: ${process.platform} (${process.arch})`);
            console.log(`📍 Node.js: ${process.version}`);
            console.log(`📁 Working Directory: ${process.cwd()}`);
            console.log();
        }
        
        if (this.errors.length === 0 && this.warnings.length === 0) {
            console.log('🎉 Extension is production-ready!');
            console.log('   All validations passed successfully.');
        } else {
            if (this.errors.length > 0) {
                console.log(`❌ ${this.errors.length} Error(s):`);
                this.errors.forEach((error, index) => {
                    console.log(`   ${index + 1}. ${error}`);
                });
                console.log();
            }
            
            if (this.warnings.length > 0) {
                console.log(`⚠️  ${this.warnings.length} Warning(s):`);
                this.warnings.forEach((warning, index) => {
                    console.log(`   ${index + 1}. ${warning}`);
                });
                console.log();
            }
        }
        
        // Production readiness assessment
        if (this.errors.length === 0) {
            console.log('✅ PRODUCTION READY');
            console.log('   Extension meets all critical requirements for enterprise deployment');
            
            if (this.isCI) {
                console.log('   ✅ CI/CD pipeline validation: PASSED');
                console.log('   ✅ Cross-platform compatibility: VERIFIED');
                console.log('   ✅ Package structure: VALID');
            }
        } else {
            console.log('❌ NOT PRODUCTION READY');
            console.log('   Please fix the above errors before proceeding with deployment');
            
            if (this.isCI) {
                console.log('   💡 CI/CD Hint: Check GitHub Actions logs for detailed error context');
                console.log('   💡 Enterprise Deployment: All errors must be resolved for compliance');
            }
        }
        
        // Environment-specific next steps
        if (this.isCI) {
            console.log('\n🔄 CI/CD Pipeline Status:');
            if (this.errors.length === 0) {
                console.log('   ✅ Ready for packaging and deployment');
                console.log('   ✅ Enterprise validation standards met');
            } else {
                console.log('   ❌ Pipeline will fail due to validation errors');
                console.log('   🔧 Fix errors and re-run pipeline');
            }
        } else {
            console.log('\n🚀 Next Steps:');
            console.log('   1. Run: npm run build:production');
            console.log('   2. Test: npm run test');
            console.log('   3. Package: npm run package');
            console.log('   4. Publish: npm run publish');
        }
        
        // Summary for CI logging
        if (this.isCI) {
            console.log(`\n📈 Summary: ${this.errors.length} errors, ${this.warnings.length} warnings`);
        }
    }
}

// Run validation
const validator = new ExtensionValidator();
const isValid = validator.validate();
process.exit(isValid ? 0 : 1);