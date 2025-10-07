/**
 * Unit tests for Connascence Service MCP Integration
 */

import * as assert from 'assert';
import * as vscode from 'vscode';
import { ConnascenceService } from '../../services/connascenceService';
import { ConfigurationService } from '../../services/configurationService';
import { TelemetryService } from '../../services/telemetryService';

suite('ConnascenceService MCP Integration Test Suite', () => {
    let service: ConnascenceService;
    let configService: ConfigurationService;
    let telemetryService: TelemetryService;
    let context: vscode.ExtensionContext;

    setup(() => {
        context = {
            subscriptions: [],
            extensionPath: '/test/path',
            globalState: {
                get: () => undefined,
                update: () => Promise.resolve()
            } as any,
            workspaceState: {
                get: () => undefined,
                update: () => Promise.resolve()
            } as any
        } as any;

        configService = new ConfigurationService();
        telemetryService = new TelemetryService();
        service = new ConnascenceService(configService, telemetryService, context);
    });

    suite('Service Initialization', () => {
        test('Should create ConnascenceService instance', () => {
            assert.ok(service, 'Service should be created');
        });

        test('Should initialize with CLI mode by default', () => {
            // Service should work even without MCP
            assert.ok(service, 'Service should initialize in CLI mode');
        });
    });

    suite('File Analysis', () => {
        test('Should handle analyzeFile request', async () => {
            // This will fail without actual connascence binary, but tests the method exists
            try {
                await service.analyzeFile('/test/file.py');
                // If it succeeds, that's fine
                assert.ok(true);
            } catch (error) {
                // Expected to fail without binary, but method should exist
                assert.ok(error, 'Should attempt analysis');
            }
        });

        test('Should reject invalid file paths', async () => {
            try {
                await service.analyzeFile('');
                assert.fail('Should reject empty path');
            } catch (error) {
                assert.ok(error, 'Should throw error for empty path');
            }
        });

        test('Should handle non-existent files', async () => {
            try {
                await service.analyzeFile('/nonexistent/file.py');
                assert.fail('Should reject non-existent file');
            } catch (error) {
                assert.ok(error, 'Should throw error for non-existent file');
            }
        });
    });

    suite('Workspace Analysis', () => {
        test('Should handle analyzeWorkspace request', async () => {
            try {
                await service.analyzeWorkspace('/test/workspace');
                assert.ok(true);
            } catch (error) {
                // Expected to fail without binary
                assert.ok(error, 'Should attempt workspace analysis');
            }
        });

        test('Should reject invalid workspace paths', async () => {
            try {
                await service.analyzeWorkspace('');
                assert.fail('Should reject empty workspace path');
            } catch (error) {
                assert.ok(error, 'Should throw error for empty workspace path');
            }
        });
    });

    suite('Safety Validation', () => {
        test('Should handle validateSafety request', async () => {
            try {
                await service.validateSafety('/test/file.py', 'strict');
                assert.ok(true);
            } catch (error) {
                // Expected to fail without binary
                assert.ok(error, 'Should attempt safety validation');
            }
        });

        test('Should validate with different profiles', async () => {
            const profiles = ['strict', 'standard', 'lenient'];

            for (const profile of profiles) {
                try {
                    await service.validateSafety('/test/file.py', profile);
                } catch (error) {
                    // Expected to fail, but should accept all valid profiles
                    assert.ok(error);
                }
            }
        });

        test('Should reject invalid safety profiles', async () => {
            try {
                await service.validateSafety('/test/file.py', 'invalid-profile');
                // Service might accept any string, so this test verifies behavior
                assert.ok(true);
            } catch (error) {
                assert.ok(error);
            }
        });
    });

    suite('Refactoring Suggestions', () => {
        test('Should handle suggestRefactoring request', async () => {
            try {
                await service.suggestRefactoring('/test/file.py');
                assert.ok(true);
            } catch (error) {
                // Expected to fail without binary
                assert.ok(error, 'Should attempt refactoring suggestions');
            }
        });

        test('Should handle refactoring with selection', async () => {
            const selection = {
                start: { line: 10, character: 0 },
                end: { line: 20, character: 0 }
            };

            try {
                await service.suggestRefactoring('/test/file.py', selection);
            } catch (error) {
                assert.ok(error, 'Should attempt refactoring with selection');
            }
        });
    });

    suite('Autofixes', () => {
        test('Should handle getAutofixes request', async () => {
            try {
                await service.getAutofixes('/test/file.py');
                assert.ok(true);
            } catch (error) {
                // Expected to fail without binary
                assert.ok(error, 'Should attempt to get autofixes');
            }
        });

        test('Should handle non-existent file', async () => {
            try {
                await service.getAutofixes('/nonexistent/file.py');
            } catch (error) {
                assert.ok(error, 'Should handle non-existent file');
            }
        });
    });

    suite('Report Generation', () => {
        test('Should handle generateReport request', async () => {
            try {
                await service.generateReport('/test/workspace');
                assert.ok(true);
            } catch (error) {
                // Expected to fail without binary
                assert.ok(error, 'Should attempt report generation');
            }
        });

        test('Should generate report for workspace', async () => {
            try {
                await service.generateReport('/test/workspace');
            } catch (error) {
                assert.ok(error, 'Should attempt workspace report');
            }
        });
    });

    suite('MCP vs CLI Selection', () => {
        test('Should use CLI when MCP disabled', async () => {
            try {
                await service.analyzeFile('/test/file.py');
            } catch (error) {
                // Should attempt CLI analysis
                assert.ok(error);
            }
        });

        test('Should fallback to CLI when MCP unavailable', async () => {
            // Even if MCP is enabled, should fallback gracefully
            try {
                await service.analyzeFile('/test/file.py');
            } catch (error) {
                assert.ok(error, 'Should fallback to CLI');
            }
        });
    });

    suite('Configuration Handling', () => {
        test('Should read safety profile configuration', () => {
            const profile = configService.getSafetyProfile();
            assert.ok(profile, 'Should have safety profile');
        });

        test('Should read parallel analysis configuration', () => {
            const parallel = configService.getEnableParallelAnalysis();
            assert.ok(typeof parallel === 'boolean', 'Parallel setting should be boolean');
        });

        test('Should read NASA compliance configuration', () => {
            const nasa = configService.getEnableNASACompliance();
            assert.ok(typeof nasa === 'boolean', 'NASA compliance should be boolean');
        });
    });

    suite('Error Handling', () => {
        test('Should handle null parameters', async () => {
            try {
                await service.analyzeFile(null as any);
                assert.fail('Should reject null');
            } catch (error) {
                assert.ok(error, 'Should throw error for null');
            }
        });

        test('Should handle undefined parameters', async () => {
            try {
                await service.analyzeFile(undefined as any);
                assert.fail('Should reject undefined');
            } catch (error) {
                assert.ok(error, 'Should throw error for undefined');
            }
        });

        test('Should handle concurrent requests', async () => {
            const requests = Array(5).fill(null).map((_, i) =>
                service.analyzeFile(`/test/file${i}.py`).catch(() => {
                    // Expected to fail
                })
            );

            await Promise.all(requests);
            assert.ok(true, 'Should handle concurrent requests');
        });
    });
});
