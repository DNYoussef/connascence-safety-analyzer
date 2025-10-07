import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Connascence Extension Test Suite', () => {
    vscode.window.showInformationMessage('Starting Connascence extension tests');

    test('Extension should be present', () => {
        const extension = vscode.extensions.getExtension('connascence-systems.connascence-safety-analyzer');
        assert.ok(extension, 'Extension should be installed');
    });

    test('Extension should activate', async () => {
        const extension = vscode.extensions.getExtension('connascence-systems.connascence-safety-analyzer');
        assert.ok(extension, 'Extension should exist');

        if (!extension.isActive) {
            await extension.activate();
        }
        assert.ok(extension.isActive, 'Extension should be active');
    });

    test('Core commands should be registered', async () => {
        const commands = await vscode.commands.getCommands(true);

        const expectedCommands = [
            'connascence.analyzeFile',
            'connascence.analyzeWorkspace',
            'connascence.validateSafety',
            'connascence.suggestRefactoring',
            'connascence.applyAutofix',
            'connascence.showDashboard',
            'connascence.refreshDashboard'
        ];

        for (const cmd of expectedCommands) {
            assert.ok(
                commands.includes(cmd),
                `Command ${cmd} should be registered`
            );
        }
    });

    test('Configuration settings should be available', () => {
        const config = vscode.workspace.getConfiguration('connascence');

        // Test that key configuration options exist
        assert.ok(config.has('safetyProfile'), 'Should have safetyProfile setting');
        assert.ok(config.has('realTimeAnalysis'), 'Should have realTimeAnalysis setting');
        assert.ok(config.has('enableIntelliSense'), 'Should have enableIntelliSense setting');

        // Test default values
        const safetyProfile = config.get('safetyProfile');
        assert.ok(safetyProfile, 'Safety profile should have a default value');
    });

    test('Enhanced pipeline configuration should be available', () => {
        const config = vscode.workspace.getConfiguration('connascence.enhancedPipeline');

        assert.ok(config.has('enableCrossPhaseCorrelation'), 'Should have cross-phase correlation setting');
        assert.ok(config.has('enableAuditTrail'), 'Should have audit trail setting');
        assert.ok(config.has('enableSmartRecommendations'), 'Should have smart recommendations setting');
    });
});
