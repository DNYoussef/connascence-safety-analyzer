#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import * as fs from 'fs-extra';
import * as path from 'path';
import { glob } from 'glob';
import { AnalysisEngine } from './analysis/engine';
import { ReportGenerator } from './reports/generator';
import { ConfigManager } from './config/manager';

const program = new Command();

program
  .name('connascence')
  .description('Connascence Safety Analyzer CLI')
  .version('1.0.0');

// Analyze command
program
  .command('analyze')
  .description('Analyze files for connascence violations')
  .argument('[files...]', 'Files or patterns to analyze')
  .option('-r, --recursive', 'Recursively analyze directories')
  .option('-f, --format <type>', 'Output format (json, table, summary)', 'table')
  .option('-o, --output <file>', 'Output file path')
  .option('--severity <level>', 'Minimum severity level (critical, major, minor, info)', 'info')
  .option('--profile <name>', 'Analysis profile to use', 'modern_general')
  .action(async (files: string[], options) => {
    const spinner = ora('Analyzing files...').start();
    
    try {
      const engine = new AnalysisEngine();
      const config = ConfigManager.load();
      
      // Determine files to analyze
      const filesToAnalyze = await getFilesToAnalyze(files, options.recursive);
      
      if (filesToAnalyze.length === 0) {
        spinner.fail('No files found to analyze');
        process.exit(1);
      }
      
      spinner.text = `Analyzing ${filesToAnalyze.length} files...`;
      
      const results = await engine.analyzeFiles(filesToAnalyze, {
        profile: options.profile,
        minSeverity: options.severity
      });
      
      spinner.succeed(`Analysis complete: ${results.totalViolations} violations found`);
      
      // Generate and output report
      const generator = new ReportGenerator();
      const report = generator.generate(results, options.format);
      
      if (options.output) {
        await fs.writeFile(options.output, report);
        console.log(chalk.green(`Report saved to ${options.output}`));
      } else {
        console.log(report);
      }
      
      // Exit with error code if critical violations found
      if (results.criticalCount > 0) {
        process.exit(1);
      }
      
    } catch (error) {
      spinner.fail(`Analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      process.exit(1);
    }
  });

// Report command
program
  .command('report')
  .description('Generate analysis report from previous results')
  .option('-i, --input <file>', 'Input analysis results file')
  .option('-f, --format <type>', 'Output format (json, html, pdf, csv)', 'html')
  .option('-o, --output <file>', 'Output file path')
  .option('--template <path>', 'Custom report template')
  .action(async (options) => {
    const spinner = ora('Generating report...').start();
    
    try {
      const generator = new ReportGenerator();
      
      let results;
      if (options.input) {
        results = await fs.readJson(options.input);
      } else {
        // Look for recent analysis results
        const recentFile = path.join(process.cwd(), '.connascence-results.json');
        if (await fs.pathExists(recentFile)) {
          results = await fs.readJson(recentFile);
        } else {
          throw new Error('No analysis results found. Run analyze command first or specify --input');
        }
      }
      
      const report = generator.generate(results, options.format, options.template);
      
      const outputFile = options.output || `connascence-report.${options.format}`;
      await fs.writeFile(outputFile, report);
      
      spinner.succeed(`Report generated: ${outputFile}`);
      
    } catch (error) {
      spinner.fail(`Report generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      process.exit(1);
    }
  });

// Config command
program
  .command('config')
  .description('Manage configuration settings')
  .option('--set <key=value>', 'Set configuration value')
  .option('--get <key>', 'Get configuration value')
  .option('--list', 'List all configuration')
  .option('--reset', 'Reset to default configuration')
  .action(async (options) => {
    const config = ConfigManager.load();
    
    if (options.set) {
      const [key, value] = options.set.split('=');
      if (!key || value === undefined) {
        console.error(chalk.red('Invalid format. Use: --set key=value'));
        process.exit(1);
      }
      
      config.set(key, value);
      await config.save();
      console.log(chalk.green(`Set ${key} = ${value}`));
      
    } else if (options.get) {
      const value = config.get(options.get);
      console.log(`${options.get} = ${value || '(not set)'}`);
      
    } else if (options.list) {
      console.log(chalk.yellow('Current Configuration:'));
      console.log(JSON.stringify(config.getAll(), null, 2));
      
    } else if (options.reset) {
      await config.reset();
      console.log(chalk.green('Configuration reset to defaults'));
      
    } else {
      console.log('Use --set, --get, --list, or --reset');
    }
  });

// MCP server command
program
  .command('mcp')
  .description('Start MCP server for AI integration')
  .option('-p, --port <number>', 'Server port', '8080')
  .option('-h, --host <address>', 'Server host', 'localhost')
  .option('--config <file>', 'Configuration file path')
  .option('--context7', 'Enable Context7 integration for API management')
  .action(async (options) => {
    const spinner = ora('Starting MCP server...').start();
    
    try {
      const { MCPServer } = await import('./mcp/server');
      
      const server = new MCPServer({
        port: parseInt(options.port),
        host: options.host,
        configFile: options.config,
        enableContext7: options.context7
      });
      
      await server.start();
      spinner.succeed(`MCP server running on http://${options.host}:${options.port}`);
      
      // Keep process alive
      process.on('SIGINT', async () => {
        console.log(chalk.yellow('\nShutting down server...'));
        await server.stop();
        process.exit(0);
      });
      
    } catch (error) {
      spinner.fail(`Failed to start MCP server: ${error instanceof Error ? error.message : 'Unknown error'}`);
      process.exit(1);
    }
  });

// Init command
program
  .command('init')
  .description('Initialize connascence configuration in current directory')
  .option('--profile <name>', 'Analysis profile to use', 'modern_general')
  .option('--mcp', 'Include MCP server configuration')
  .action(async (options) => {
    const spinner = ora('Initializing connascence configuration...').start();
    
    try {
      const configPath = path.join(process.cwd(), '.connascence.json');
      const mcpConfigPath = path.join(process.cwd(), 'mcp-config.json');
      
      // Create base configuration
      const config = {
        profile: options.profile,
        safetyLevel: 'modern_general',
        realTimeAnalysis: true,
        aiIntegration: true,
        serverUrl: 'http://localhost:8080',
        excludePatterns: [
          'node_modules/**',
          '**/*.min.js',
          '**/*.d.ts',
          'dist/**',
          'build/**'
        ],
        includeLanguages: ['python', 'javascript', 'typescript', 'c', 'cpp']
      };
      
      await fs.writeJson(configPath, config, { spaces: 2 });
      
      // Create MCP configuration if requested
      if (options.mcp) {
        const mcpConfig = {
          server: {
            port: 8080,
            host: 'localhost',
            cors: true
          },
          ai: {
            providers: {
              openai: {
                enabled: false,
                apiKey: '${OPENAI_API_KEY}',
                model: 'gpt-4'
              },
              anthropic: {
                enabled: false,
                apiKey: '${ANTHROPIC_API_KEY}',
                model: 'claude-3-sonnet-20240229'
              },
              google: {
                enabled: false,
                apiKey: '${GOOGLE_AI_API_KEY}',
                model: 'gemini-pro'
              }
            },
            context7: {
              enabled: true,
              endpoint: 'https://api.context7.ai/v1',
              features: ['api-discovery', 'rate-limiting', 'cost-tracking']
            }
          },
          features: {
            caching: true,
            rateLimit: {
              requests: 100,
              window: '1h'
            },
            logging: {
              level: 'info',
              file: 'connascence-mcp.log'
            }
          }
        };
        
        await fs.writeJson(mcpConfigPath, mcpConfig, { spaces: 2 });
      }
      
      spinner.succeed('Configuration initialized');
      console.log(chalk.green('Created:'));
      console.log(`  ${configPath}`);
      if (options.mcp) {
        console.log(`  ${mcpConfigPath}`);
      }
      
      console.log(chalk.yellow('\nNext steps:'));
      console.log('1. Configure your API keys in mcp-config.json');
      console.log('2. Start MCP server: connascence mcp --config mcp-config.json');
      console.log('3. Run analysis: connascence analyze .');
      
    } catch (error) {
      spinner.fail(`Initialization failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      process.exit(1);
    }
  });

async function getFilesToAnalyze(files: string[], recursive: boolean): Promise<string[]> {
  if (files.length === 0) {
    // Default patterns
    files = recursive ? ['**/*.{py,js,ts,c,cpp,h,hpp}'] : ['*.{py,js,ts,c,cpp,h,hpp}'];
  }
  
  const allFiles: string[] = [];
  
  for (const pattern of files) {
    const stat = await fs.stat(pattern).catch(() => null);
    
    if (stat?.isFile()) {
      allFiles.push(pattern);
    } else if (stat?.isDirectory() && recursive) {
      const dirFiles = await glob(path.join(pattern, '**/*.{py,js,ts,c,cpp,h,hpp}'));
      allFiles.push(...dirFiles);
    } else {
      const globFiles = await glob(pattern, { ignore: 'node_modules/**' });
      allFiles.push(...globFiles);
    }
  }
  
  return [...new Set(allFiles)]; // Remove duplicates
}

program.parse();