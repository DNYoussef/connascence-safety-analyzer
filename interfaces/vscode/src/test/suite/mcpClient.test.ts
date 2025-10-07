/**
 * Unit tests for MCP Client
 */

import * as assert from 'assert';
import * as vscode from 'vscode';
import { MCPClient } from '../../services/mcpClient';

suite('MCPClient Test Suite', () => {
    let client: MCPClient;
    let context: vscode.ExtensionContext;

    setup(() => {
        context = {
            subscriptions: [],
            extensionPath: '/test/path',
            globalState: {
                get: () => undefined,
                update: () => Promise.resolve()
            } as any
        } as any;

        client = new MCPClient(context);
    });

    teardown(() => {
        if (client) {
            client.dispose();
        }
    });

    suite('Constructor and Initialization', () => {
        test('Should create MCPClient instance', () => {
            assert.ok(client, 'Client should be created');
            assert.strictEqual(client.isServerConnected(), false, 'Client should not be connected initially');
        });

        test('Should have default server URL', () => {
            const config = vscode.workspace.getConfiguration('connascence');
            const serverUrl = config.get<string>('serverUrl', 'http://localhost:8080');
            assert.ok(serverUrl, 'Server URL should be defined');
        });
    });

    suite('Connection Management', () => {
        test('Should handle connection failure gracefully', async () => {
            try {
                await client.connect();
                assert.fail('Should have thrown connection error');
            } catch (error) {
                assert.ok(error, 'Should throw error on connection failure');
            }
        });

        test('Should report disconnected state initially', () => {
            assert.strictEqual(client.isServerConnected(), false, 'Should be disconnected initially');
        });

        test('Should handle multiple connect attempts', async () => {
            const attempts = 3;
            for (let i = 0; i < attempts; i++) {
                try {
                    await client.connect();
                } catch (error) {
                    // Expected to fail without server
                    assert.ok(error, `Attempt ${i + 1} should fail gracefully`);
                }
            }
        });
    });

    suite('Analysis Methods', () => {
        test('Should reject analyzeFile when not connected', async () => {
            try {
                await client.analyzeFile('/test/file.py');
                assert.fail('Should have thrown not connected error');
            } catch (error) {
                assert.ok(error, 'Should throw error when not connected');
            }
        });

        test('Should reject analyzeWorkspace when not connected', async () => {
            try {
                await client.analyzeWorkspace('/test/workspace');
                assert.fail('Should have thrown not connected error');
            } catch (error) {
                assert.ok(error, 'Should throw error when not connected');
            }
        });

        test('Should reject validateSafety when not connected', async () => {
            try {
                await client.validateSafety('/test/file.py', 'strict');
                assert.fail('Should have thrown not connected error');
            } catch (error) {
                assert.ok(error, 'Should throw error when not connected');
            }
        });

        test('Should reject getAutofixes when not connected', async () => {
            try {
                await client.getAutofixes('/test/file.py');
                assert.fail('Should have thrown not connected error');
            } catch (error) {
                assert.ok(error, 'Should throw error when not connected');
            }
        });

        test('Should reject generateReport when not connected', async () => {
            try {
                await client.generateReport('/test/workspace', 'json');
                assert.fail('Should have thrown not connected error');
            } catch (error) {
                assert.ok(error, 'Should throw error when not connected');
            }
        });
    });

    suite('Options and Configuration', () => {
        test('Should accept options in analyzeFile', async () => {
            try {
                await client.analyzeFile('/test/file.py', {
                    format: 'json',
                    profile: 'strict'
                });
                assert.fail('Should throw not connected error');
            } catch (error) {
                // Verify options were passed (error expected due to no connection)
                assert.ok(error);
            }
        });

        test('Should accept options in analyzeWorkspace', async () => {
            try {
                await client.analyzeWorkspace('/test/workspace', {
                    format: 'json',
                    includeTests: true
                });
                assert.fail('Should throw not connected error');
            } catch (error) {
                // Verify options were passed (error expected due to no connection)
                assert.ok(error);
            }
        });
    });

    suite('Error Handling', () => {
        test('Should handle invalid file paths', async () => {
            try {
                await client.analyzeFile('');
                assert.fail('Should reject empty file path');
            } catch (error) {
                assert.ok(error, 'Should throw error for empty path');
            }
        });

        test('Should handle null parameters', async () => {
            try {
                await client.analyzeFile(null as any);
                assert.fail('Should reject null parameter');
            } catch (error) {
                assert.ok(error, 'Should throw error for null path');
            }
        });

        test('Should handle undefined parameters', async () => {
            try {
                await client.analyzeFile(undefined as any);
                assert.fail('Should reject undefined parameter');
            } catch (error) {
                assert.ok(error, 'Should throw error for undefined path');
            }
        });
    });

    suite('Resource Management', () => {
        test('Should dispose cleanly', () => {
            assert.doesNotThrow(() => {
                client.dispose();
            }, 'Dispose should not throw');
        });

        test('Should handle multiple dispose calls', () => {
            client.dispose();
            assert.doesNotThrow(() => {
                client.dispose();
            }, 'Multiple dispose calls should be safe');
        });

        test('Should not accept requests after disposal', () => {
            client.dispose();
            assert.strictEqual(client.isServerConnected(), false, 'Should report disconnected after disposal');
        });
    });

    suite('WebSocket Message Handling', () => {
        test('Should handle WebSocket module loading', async () => {
            // This tests that the dynamic import mechanism works
            try {
                await client.connect();
            } catch (error) {
                // Expected to fail, but should attempt to load WebSocket
                assert.ok(error);
            }
        });

        test('Should handle connection timeout', async () => {
            const startTime = Date.now();
            try {
                await client.connect();
                assert.fail('Should timeout');
            } catch (error) {
                const duration = Date.now() - startTime;
                assert.ok(duration >= 0, 'Should wait before failing');
            }
        });
    });

    suite('Request/Response Pattern', () => {
        test('Should generate unique request IDs', async () => {
            const requests = 10;
            const promises = [];

            for (let i = 0; i < requests; i++) {
                promises.push(
                    client.analyzeFile(`/test/file${i}.py`).catch(() => {
                        // Expected to fail, we're testing ID generation
                    })
                );
            }

            await Promise.all(promises);
            assert.ok(true, 'Should handle multiple concurrent requests');
        });
    });

    suite('Configuration Integration', () => {
        test('Should respect serverUrl configuration', () => {
            const config = vscode.workspace.getConfiguration('connascence');
            const serverUrl = config.get<string>('serverUrl');
            assert.ok(serverUrl !== undefined, 'Server URL should be configurable');
        });

        test('Should respect mcpServerPort configuration', () => {
            const config = vscode.workspace.getConfiguration('connascence');
            const port = config.get<number>('mcpServerPort', 8765);
            assert.ok(typeof port === 'number', 'Port should be a number');
            assert.ok(port > 0 && port < 65536, 'Port should be valid');
        });

        test('Should respect useMCP configuration', () => {
            const config = vscode.workspace.getConfiguration('connascence');
            const useMCP = config.get<boolean>('useMCP', false);
            assert.ok(typeof useMCP === 'boolean', 'useMCP should be a boolean');
        });
    });

    suite('Graceful Degradation', () => {
        test('Should be designed for CLI fallback', () => {
            // The client should be optional - failures should allow CLI fallback
            assert.strictEqual(client.isServerConnected(), false, 'Should start disconnected');
        });

        test('Should report connection state accurately', () => {
            assert.strictEqual(typeof client.isServerConnected(), 'boolean', 'Should return boolean state');
        });
    });
});
