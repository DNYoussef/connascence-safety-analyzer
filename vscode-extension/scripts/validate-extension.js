#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Validation script for the Connascence VS Code extension
 */
class ExtensionValidator {
    constructor() {
        this.basePath = path.join(__dirname, '..');
        this.errors = [];
        this.warnings = [];
    }

    validate() {
        console.log('🔍 Validating Connascence VS Code Extension...\n');
        
        this.validatePackageJson();
        this.validateTypeScript();
        this.validateWebpack();
        this.validateSourceStructure();
        this.validateConfiguration();
        this.validateReadme();
        
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

    printResults() {
        console.log('\n📊 Validation Results:');
        console.log('═══════════════════════');
        
        if (this.errors.length === 0 && this.warnings.length === 0) {
            console.log('🎉 Extension is production-ready!');
            console.log('   All validations passed successfully.');
        } else {
            if (this.errors.length > 0) {
                console.log(`❌ ${this.errors.length} Error(s):`);
                this.errors.forEach(error => console.log(`   • ${error}`));
                console.log();
            }
            
            if (this.warnings.length > 0) {
                console.log(`⚠️  ${this.warnings.length} Warning(s):`);
                this.warnings.forEach(warning => console.log(`   • ${warning}`));
                console.log();
            }
        }
        
        // Production readiness assessment
        if (this.errors.length === 0) {
            console.log('✅ PRODUCTION READY');
            console.log('   Extension meets all critical requirements');
        } else {
            console.log('❌ NOT PRODUCTION READY');
            console.log('   Please fix errors before publishing');
        }
        
        console.log('\n🚀 Next Steps:');
        console.log('   1. Run: npm run build:production');
        console.log('   2. Test: npm run test');
        console.log('   3. Package: npm run package');
        console.log('   4. Publish: npm run publish');
    }
}

// Run validation
const validator = new ExtensionValidator();
const isValid = validator.validate();
process.exit(isValid ? 0 : 1);