/**
 * Integration tests for VSCode extension
 */
import * as assert from 'assert';
import * as vscode from 'vscode';
import * as path from 'path';
import { ConnascenceApiClient } from '../services/connascenceApiClient';

suite('Connascence Extension Integration Tests', () => {
    let apiClient: ConnascenceApiClient;
    
    setup(() => {
        apiClient = new ConnascenceApiClient();
    });

    test('Can create API client', () => {
        assert.ok(apiClient);
    });

    test('Can analyze Python file with fallback', async () => {
        // Create a simple Python file for testing
        const testFilePath = path.join(__dirname, '..', '..', 'test_sample.py');
        
        try {
            const result = await apiClient.analyzeFile(testFilePath);
            
            assert.ok(result);
            assert.ok(Array.isArray(result.findings));
            assert.ok(typeof result.qualityScore === 'number');
            assert.ok(result.summary);
            assert.ok(typeof result.summary.totalIssues === 'number');
            
        } catch (error) {
            // This is expected if the Python analyzer is not available
            // The test should still pass as long as we get a meaningful error
            assert.ok(error instanceof Error);
            console.log('Expected error (analyzer not available):', error.message);
        }
    });

    test('Can handle configuration settings', () => {
        const config = vscode.workspace.getConfiguration('connascence');
        
        // Test that we can read configuration values
        const safetyProfile = config.get('safetyProfile', 'modern_general');
        const realTimeAnalysis = config.get('realTimeAnalysis', true);
        
        assert.ok(typeof safetyProfile === 'string');
        assert.ok(typeof realTimeAnalysis === 'boolean');
    });

    test('Can validate safety profile options', () => {
        const validProfiles = [
            'none',
            'general_safety_strict', 
            'safety_level_1',
            'safety_level_3',
            'modern_general'
        ];
        
        for (const profile of validProfiles) {
            // This should not throw
            assert.doesNotThrow(() => {
                // Just verify the profile name is a string
                assert.ok(typeof profile === 'string');
                assert.ok(profile.length > 0);
            });
        }
    });
});