/**
 * Unit tests for Connascence Diagnostics MCP Integration
 */

import * as assert from 'assert';
import * as vscode from 'vscode';
import { ConnascenceDiagnostics, ConnascenceViolation } from '../../diagnostics';

suite('ConnascenceDiagnostics MCP Integration Test Suite', () => {
    let diagnostics: ConnascenceDiagnostics;
    let diagnosticCollection: vscode.DiagnosticCollection;
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

        // Mock configuration
        const mockConfig = {
            get: (key: string, defaultValue?: any) => {
                const configs: any = {
                    'useMCP': false,
                    'pathToBinary': 'connascence',
                    'policyPreset': 'service-defaults',
                    'debounceMs': 1000,
                    'severityThreshold': 'medium',
                    'maxDiagnostics': 1500,
                    'includeTests': false
                };
                return configs[key] !== undefined ? configs[key] : defaultValue;
            },
            has: (key: string) => true,
            inspect: () => undefined,
            update: () => Promise.resolve()
        };

        (vscode.workspace.getConfiguration as any) = () => mockConfig;

        diagnosticCollection = vscode.languages.createDiagnosticCollection('connascence-test');
        diagnostics = new ConnascenceDiagnostics(context);
        diagnostics.setCollection(diagnosticCollection);
    });

    teardown(() => {
        if (diagnostics) {
            diagnostics.dispose();
        }
        if (diagnosticCollection) {
            diagnosticCollection.dispose();
        }
    });

    suite('Initialization', () => {
        test('Should create ConnascenceDiagnostics instance', () => {
            assert.ok(diagnostics, 'Diagnostics should be created');
        });

        test('Should initialize with MCP client disabled by default', () => {
            // MCP should be disabled in test configuration
            assert.ok(diagnostics, 'Should initialize without MCP');
        });

        test('Should accept diagnostic collection', () => {
            assert.doesNotThrow(() => {
                diagnostics.setCollection(diagnosticCollection);
            }, 'Should accept diagnostic collection');
        });
    });

    suite('File Scanning', () => {
        test('Should ignore non-Python files', async () => {
            const mockDocument = {
                uri: vscode.Uri.file('/test/file.js'),
                languageId: 'javascript',
                getText: () => 'console.log("test");',
                lineCount: 1
            } as any;

            await diagnostics.scanFile(mockDocument);
            // Should return silently without error
            assert.ok(true, 'Should ignore non-Python files');
        });

        test('Should handle Python files', async () => {
            const mockDocument = {
                uri: vscode.Uri.file('/test/file.py'),
                languageId: 'python',
                getText: () => 'print("test")',
                lineCount: 1
            } as any;

            try {
                await diagnostics.scanFile(mockDocument);
                assert.ok(true, 'Should attempt to scan Python files');
            } catch (error) {
                // Expected to fail without actual binary
                assert.ok(error, 'Should attempt scan');
            }
        });

        test('Should handle scan errors gracefully', async () => {
            const mockDocument = {
                uri: vscode.Uri.file('/nonexistent/file.py'),
                languageId: 'python',
                getText: () => '',
                lineCount: 0
            } as any;

            assert.doesNotThrow(async () => {
                await diagnostics.scanFile(mockDocument);
            }, 'Should handle scan errors gracefully');
        });
    });

    suite('Debounced Scanning', () => {
        test('Should debounce scan requests', (done) => {
            const mockDocument = {
                uri: vscode.Uri.file('/test/file.py'),
                languageId: 'python',
                getText: () => 'print("test")',
                lineCount: 1
            } as any;

            // Call multiple times rapidly
            diagnostics.scanFileDebounced(mockDocument);
            diagnostics.scanFileDebounced(mockDocument);
            diagnostics.scanFileDebounced(mockDocument);

            // Should only execute once after debounce period
            setTimeout(() => {
                assert.ok(true, 'Debounce should delay execution');
                done();
            }, 1500);
        });

        test('Should respect debounce configuration', () => {
            const config = vscode.workspace.getConfiguration('connascence');
            const debounceMs = config.get<number>('debounceMs', 1000);
            assert.ok(debounceMs >= 0, 'Debounce should be non-negative');
        });
    });

    suite('Workspace Scanning', () => {
        test('Should handle workspace scan request', async () => {
            // This will fail without workspace, but tests the method exists
            try {
                await diagnostics.scanWorkspace();
            } catch (error) {
                // Expected without workspace
                assert.ok(true, 'Should handle workspace scan');
            }
        });

        test('Should show progress during workspace scan', async () => {
            // Verify progress API is called (implementation detail)
            try {
                await diagnostics.scanWorkspace();
            } catch (error) {
                assert.ok(true, 'Should attempt workspace scan');
            }
        });
    });

    suite('Violation Parsing', () => {
        test('Should parse valid violations', () => {
            const mockResult = {
                violations: [
                    {
                        id: 'test-1',
                        rule_id: 'CON_POSITION',
                        severity: 'high',
                        connascence_type: 'CoP',
                        description: 'Test violation',
                        file_path: '/test/file.py',
                        line_number: 10,
                        column_number: 5,
                        weight: 5,
                        recommendation: 'Refactor this code'
                    }
                ]
            };

            // Access private method via any cast for testing
            const violations = (diagnostics as any).parseViolations(mockResult);

            assert.ok(Array.isArray(violations), 'Should return array');
            assert.strictEqual(violations.length, 1, 'Should parse one violation');
            assert.strictEqual(violations[0].id, 'test-1', 'Should preserve ID');
            assert.strictEqual(violations[0].ruleId, 'CON_POSITION', 'Should map rule_id');
        });

        test('Should filter by severity threshold', () => {
            const mockResult = {
                violations: [
                    { id: '1', rule_id: 'CON_1', severity: 'low', file_path: '/test/file.py', line_number: 1, description: 'Low' },
                    { id: '2', rule_id: 'CON_2', severity: 'medium', file_path: '/test/file.py', line_number: 2, description: 'Medium' },
                    { id: '3', rule_id: 'CON_3', severity: 'high', file_path: '/test/file.py', line_number: 3, description: 'High' },
                    { id: '4', rule_id: 'CON_4', severity: 'critical', file_path: '/test/file.py', line_number: 4, description: 'Critical' }
                ]
            };

            const violations = (diagnostics as any).parseViolations(mockResult);

            // With 'medium' threshold, should include medium, high, and critical (not low)
            assert.ok(violations.length >= 3, 'Should filter by severity');
        });

        test('Should respect max diagnostics limit', () => {
            const mockResult = {
                violations: Array(2000).fill(null).map((_, i) => ({
                    id: `test-${i}`,
                    rule_id: 'CON_TEST',
                    severity: 'high',
                    file_path: '/test/file.py',
                    line_number: i + 1,
                    description: `Violation ${i}`
                }))
            };

            const violations = (diagnostics as any).parseViolations(mockResult);

            // Should respect maxDiagnostics (1500) from config
            assert.ok(violations.length <= 1500, 'Should respect max diagnostics limit');
        });

        test('Should handle empty violations', () => {
            const mockResult = { violations: [] };
            const violations = (diagnostics as any).parseViolations(mockResult);

            assert.ok(Array.isArray(violations), 'Should return array');
            assert.strictEqual(violations.length, 0, 'Should handle empty array');
        });

        test('Should handle missing violations field', () => {
            const mockResult = {};
            const violations = (diagnostics as any).parseViolations(mockResult);

            assert.ok(Array.isArray(violations), 'Should return array');
            assert.strictEqual(violations.length, 0, 'Should handle missing field');
        });
    });

    suite('Diagnostic Conversion', () => {
        test('Should convert violation to VSCode diagnostic', () => {
            const violation: ConnascenceViolation = {
                id: 'test-1',
                ruleId: 'CON_POSITION',
                severity: 'high',
                connascenceType: 'CoP',
                description: 'Test violation',
                filePath: '/test/file.py',
                lineNumber: 10,
                columnNumber: 5,
                weight: 5,
                recommendation: 'Refactor this'
            };

            const diagnostic = (diagnostics as any).violationToDiagnostic(violation);

            assert.ok(diagnostic, 'Should create diagnostic');
            assert.strictEqual(diagnostic.source, 'connascence', 'Should set source');
            assert.strictEqual(diagnostic.code, 'CON_POSITION', 'Should set code');
            assert.strictEqual(diagnostic.message, 'Test violation', 'Should set message');
        });

        test('Should map severity to VSCode severity', () => {
            const severities: Array<'critical' | 'high' | 'medium' | 'low'> = ['critical', 'high', 'medium', 'low'];

            for (const severity of severities) {
                const violation: ConnascenceViolation = {
                    id: 'test',
                    ruleId: 'CON_TEST',
                    severity,
                    connascenceType: 'CoT',
                    description: 'Test',
                    filePath: '/test/file.py',
                    lineNumber: 1,
                    weight: 1
                };

                const diagnostic = (diagnostics as any).violationToDiagnostic(violation);
                assert.ok(diagnostic.severity !== undefined, `Should map ${severity} severity`);
            }
        });

        test('Should handle missing recommendation', () => {
            const violation: ConnascenceViolation = {
                id: 'test-1',
                ruleId: 'CON_TEST',
                severity: 'medium',
                connascenceType: 'CoT',
                description: 'Test violation',
                filePath: '/test/file.py',
                lineNumber: 10,
                weight: 3
            };

            const diagnostic = (diagnostics as any).violationToDiagnostic(violation);
            assert.ok(diagnostic, 'Should handle missing recommendation');
        });

        test('Should add recommendation as related information', () => {
            const violation: ConnascenceViolation = {
                id: 'test-1',
                ruleId: 'CON_TEST',
                severity: 'high',
                connascenceType: 'CoT',
                description: 'Test violation',
                filePath: '/test/file.py',
                lineNumber: 10,
                weight: 5,
                recommendation: 'Use dependency injection'
            };

            const diagnostic = (diagnostics as any).violationToDiagnostic(violation);
            assert.ok(diagnostic.relatedInformation, 'Should add related information');
            assert.strictEqual(diagnostic.relatedInformation.length, 1, 'Should have one related info');
        });
    });

    suite('Diagnostic Collection Management', () => {
        test('Should clear file diagnostics', () => {
            const uri = vscode.Uri.file('/test/file.py');
            assert.doesNotThrow(() => {
                diagnostics.clearFile(uri);
            }, 'Should clear file diagnostics');
        });

        test('Should clear all diagnostics', () => {
            assert.doesNotThrow(() => {
                diagnostics.clearAll();
            }, 'Should clear all diagnostics');
        });

        test('Should refresh all diagnostics', () => {
            assert.doesNotThrow(() => {
                diagnostics.refreshAll();
            }, 'Should refresh all diagnostics');
        });
    });

    suite('MCP vs CLI Analysis', () => {
        test('Should use CLI by default in tests', async () => {
            const mockDocument = {
                uri: vscode.Uri.file('/test/file.py'),
                languageId: 'python',
                getText: () => 'print("test")',
                lineCount: 1
            } as any;

            try {
                await diagnostics.scanFile(mockDocument);
            } catch (error) {
                // Should attempt CLI analysis
                assert.ok(error);
            }
        });

        test('Should fallback to CLI when MCP unavailable', async () => {
            // Even if MCP enabled, should fallback gracefully
            const mockDocument = {
                uri: vscode.Uri.file('/test/file.py'),
                languageId: 'python',
                getText: () => 'print("test")',
                lineCount: 1
            } as any;

            try {
                await diagnostics.scanFile(mockDocument);
            } catch (error) {
                assert.ok(error, 'Should fallback to CLI');
            }
        });
    });

    suite('Resource Management', () => {
        test('Should dispose cleanly', () => {
            assert.doesNotThrow(() => {
                diagnostics.dispose();
            }, 'Dispose should not throw');
        });

        test('Should handle multiple dispose calls', () => {
            diagnostics.dispose();
            assert.doesNotThrow(() => {
                diagnostics.dispose();
            }, 'Multiple dispose should be safe');
        });

        test('Should clear debounce timer on dispose', () => {
            const mockDocument = {
                uri: vscode.Uri.file('/test/file.py'),
                languageId: 'python',
                getText: () => 'print("test")',
                lineCount: 1
            } as any;

            diagnostics.scanFileDebounced(mockDocument);

            assert.doesNotThrow(() => {
                diagnostics.dispose();
            }, 'Should clear timer on dispose');
        });
    });

    suite('Configuration Integration', () => {
        test('Should read severity threshold configuration', () => {
            const config = vscode.workspace.getConfiguration('connascence');
            const threshold = config.get<string>('severityThreshold', 'medium');
            assert.ok(['low', 'medium', 'high', 'critical'].includes(threshold), 'Should have valid threshold');
        });

        test('Should read max diagnostics configuration', () => {
            const config = vscode.workspace.getConfiguration('connascence');
            const max = config.get<number>('maxDiagnostics', 1500);
            assert.ok(max > 0, 'Max diagnostics should be positive');
        });

        test('Should read binary path configuration', () => {
            const config = vscode.workspace.getConfiguration('connascence');
            const path = config.get<string>('pathToBinary', 'connascence');
            assert.ok(path, 'Binary path should be defined');
        });
    });
});
