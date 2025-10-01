import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Extension Test Suite', () => {
    vscode.window.showInformationMessage('Start all tests.');

    test('Extension should be present', () => {
        assert.ok(vscode.extensions.getExtension('connascence-systems.connascence-safety-analyzer'));
    });

    test('Extension should activate', async () => {
        const extension = vscode.extensions.getExtension('connascence-systems.connascence-safety-analyzer');
        assert.ok(extension);

        if (!extension.isActive) {
            await extension.activate();
        }
        assert.ok(extension.isActive);
    });

    test('Commands should be registered', async () => {
        const commands = await vscode.commands.getCommands(true);

        assert.ok(commands.includes('connascence.analyze'));
        assert.ok(commands.includes('connascence.showReport'));
        assert.ok(commands.includes('connascence.fix'));
        assert.ok(commands.includes('connascence.configure'));
    });
});
