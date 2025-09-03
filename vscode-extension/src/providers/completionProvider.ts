import * as vscode from 'vscode';
import { ConnascenceService } from '../services/connascenceService';

/**
 * IntelliSense completion provider for connascence-aware code suggestions
 */
export class ConnascenceCompletionProvider implements vscode.CompletionItemProvider {
    
    constructor(private connascenceService: ConnascenceService) {}

    public async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): Promise<vscode.CompletionItem[] | null> {
        
        if (token.isCancellationRequested) {
            return null;
        }

        const completions: vscode.CompletionItem[] = [];
        
        try {
            // Get line text up to cursor
            const line = document.lineAt(position);
            const textBeforeCursor = line.text.substring(0, position.character);
            const wordRange = document.getWordRangeAtPosition(position);
            
            // Add connascence-aware completions based on context
            completions.push(...this.getConnascenceCompletions(textBeforeCursor, position));
            
            // Add safe pattern completions
            if (document.languageId === 'python') {
                completions.push(...this.getPythonSafePatterns(textBeforeCursor, position));
            } else if (['javascript', 'typescript'].includes(document.languageId)) {
                completions.push(...this.getJavaScriptSafePatterns(textBeforeCursor, position));
            }
            
            // Add refactoring suggestions for common connascence violations
            completions.push(...this.getRefactoringCompletions(textBeforeCursor, position));
            
            return completions;
            
        } catch (error) {
            console.error('Error providing completions:', error);
            return [];
        }
    }

    private getConnascenceCompletions(textBeforeCursor: string, position: vscode.Position): vscode.CompletionItem[] {
        const completions: vscode.CompletionItem[] = [];
        
        // Type annotation completions to reduce CoT (Connascence of Type)
        if (textBeforeCursor.includes('def ') && textBeforeCursor.includes('(') && !textBeforeCursor.includes('):')) {
            completions.push({
                label: '→ Add Type Annotations',
                kind: vscode.CompletionItemKind.Snippet,
                insertText: new vscode.SnippetString('${1:param}: ${2:type}'),
                documentation: new vscode.MarkdownString(
                    'Add type annotations to reduce **Connascence of Type** violations\\n\\n' +
                    'Type annotations make parameter and return types explicit, reducing coupling.'
                ),
                detail: 'Connascence: Reduce CoT violations',
                sortText: '0000' // High priority
            });
        }
        
        // Constant extraction for magic numbers/strings
        if (/\b\d+\b|\b['"`][^'"`]*['"`]\b/.test(textBeforeCursor)) {
            completions.push({
                label: '→ Extract to Constant',
                kind: vscode.CompletionItemKind.Refactor,
                insertText: new vscode.SnippetString('${1:CONSTANT_NAME} = ${2:value}\\n'),
                documentation: new vscode.MarkdownString(
                    'Extract magic literals to constants to reduce **Connascence of Meaning**\\n\\n' +
                    'This makes the code more maintainable and reduces coupling to specific values.'
                ),
                detail: 'Connascence: Reduce CoM violations',
                sortText: '0001'
            });
        }
        
        // Parameter object pattern for long parameter lists
        if (textBeforeCursor.includes('def ') && (textBeforeCursor.match(/,/g) || []).length >= 3) {
            completions.push({
                label: '→ Use Parameter Object',
                kind: vscode.CompletionItemKind.Refactor,
                insertText: new vscode.SnippetString('${1:config}: ${2:ConfigType}'),
                documentation: new vscode.MarkdownString(
                    'Replace long parameter lists with parameter objects to reduce **Connascence of Position**\\n\\n' +
                    'This makes function calls more readable and reduces parameter ordering dependencies.'
                ),
                detail: 'Connascence: Reduce CoP violations',
                sortText: '0002'
            });
        }
        
        return completions;
    }

    private getPythonSafePatterns(textBeforeCursor: string, position: vscode.Position): vscode.CompletionItem[] {
        const completions: vscode.CompletionItem[] = [];
        
        // Dataclass pattern for reducing coupling
        if (textBeforeCursor.includes('class ')) {
            completions.push({
                label: '@dataclass',
                kind: vscode.CompletionItemKind.Decorator,
                insertText: new vscode.SnippetString('@dataclass\\nclass ${1:ClassName}:\\n    ${2:field}: ${3:type}'),
                documentation: new vscode.MarkdownString(
                    'Use dataclass to reduce constructor coupling and improve type safety'
                ),
                detail: 'Connascence: Safe pattern',
                filterText: 'dataclass',
                sortText: '0010'
            });
        }
        
        // Enum pattern for constants
        if (textBeforeCursor.includes('from enum import') || textBeforeCursor.includes('import enum')) {
            completions.push({
                label: 'Enum Class',
                kind: vscode.CompletionItemKind.Class,
                insertText: new vscode.SnippetString('class ${1:Status}(Enum):\\n    ${2:PENDING} = \"${3:pending}\"\\n    ${4:COMPLETE} = \"${5:complete}\"'),
                documentation: new vscode.MarkdownString(
                    'Use Enum to replace magic strings and reduce Connascence of Meaning'
                ),
                detail: 'Connascence: Safe constants pattern',
                sortText: '0011'
            });
        }
        
        // Context manager pattern
        if (textBeforeCursor.includes('with ')) {
            completions.push({
                label: '→ Custom Context Manager',
                kind: vscode.CompletionItemKind.Method,
                insertText: new vscode.SnippetString(
                    'def ${1:context_manager}():\\n' +
                    '    """Context manager to ensure proper resource cleanup"""\\n' +
                    '    try:\\n' +
                    '        ${2:# setup}\\n' +
                    '        yield ${3:resource}\\n' +
                    '    finally:\\n' +
                    '        ${4:# cleanup}'
                ),
                documentation: new vscode.MarkdownString(
                    'Create context manager to reduce temporal coupling and ensure cleanup'
                ),
                detail: 'Connascence: Safe resource pattern',
                sortText: '0012'
            });
        }
        
        return completions;
    }

    private getJavaScriptSafePatterns(textBeforeCursor: string, position: vscode.Position): vscode.CompletionItem[] {
        const completions: vscode.CompletionItem[] = [];
        
        // Object destructuring for parameter objects
        if (textBeforeCursor.includes('function ') || textBeforeCursor.includes('const ') && textBeforeCursor.includes('=')) {
            completions.push({
                label: '→ Object Destructuring',
                kind: vscode.CompletionItemKind.Snippet,
                insertText: new vscode.SnippetString('{ ${1:prop1}, ${2:prop2} }'),
                documentation: new vscode.MarkdownString(
                    'Use object destructuring to reduce parameter position coupling'
                ),
                detail: 'Connascence: Reduce CoP',
                sortText: '0020'
            });
        }
        
        // Const assertions for type safety
        if (textBeforeCursor.includes('const ') && !textBeforeCursor.includes('as const')) {
            completions.push({
                label: 'as const',
                kind: vscode.CompletionItemKind.Keyword,
                insertText: ' as const',
                documentation: new vscode.MarkdownString(
                    'Add const assertion to improve type inference and reduce type coupling'
                ),
                detail: 'TypeScript: Better type safety',
                sortText: '0021'
            });
        }
        
        // Optional chaining for safer property access
        if (textBeforeCursor.includes('.') && !textBeforeCursor.includes('?.')) {
            completions.push({
                label: '→ Optional Chaining',
                kind: vscode.CompletionItemKind.Operator,
                insertText: '?.',
                documentation: new vscode.MarkdownString(
                    'Use optional chaining to reduce structural coupling and prevent runtime errors'
                ),
                detail: 'Connascence: Safer property access',
                sortText: '0022'
            });
        }
        
        return completions;
    }

    private getRefactoringCompletions(textBeforeCursor: string, position: vscode.Position): vscode.CompletionItem[] {
        const completions: vscode.CompletionItem[] = [];
        
        // Factory pattern for complex object creation
        if (textBeforeCursor.includes('new ') || textBeforeCursor.includes('class ')) {
            completions.push({
                label: '→ Factory Method',
                kind: vscode.CompletionItemKind.Method,
                insertText: new vscode.SnippetString(
                    'static create${1:Type}(${2:config}) {\\n' +
                    '    return new ${3:ClassName}(${4:...config});\\n}'
                ),
                documentation: new vscode.MarkdownString(
                    'Use factory method to reduce constructor coupling and centralize creation logic'
                ),
                detail: 'Connascence: Reduce creation coupling',
                sortText: '0030'
            });
        }
        
        // Builder pattern for complex configurations
        if ((textBeforeCursor.match(/,/g) || []).length >= 4) {
            completions.push({
                label: '→ Builder Pattern',
                kind: vscode.CompletionItemKind.Class,
                insertText: new vscode.SnippetString(
                    'class ${1:Builder} {\\n' +
                    '    set${2:Property}(value) {\\n' +
                    '        this.${3:property} = value;\\n' +
                    '        return this;\\n' +
                    '    }\\n' +
                    '    build() {\\n' +
                    '        return new ${4:Target}(this);\\n' +
                    '    }\\n}'
                ),
                documentation: new vscode.MarkdownString(
                    'Use builder pattern to reduce parameter coupling and improve readability'
                ),
                detail: 'Connascence: Fluent interface pattern',
                sortText: '0031'
            });
        }
        
        return completions;
    }

    public resolveCompletionItem(
        item: vscode.CompletionItem,
        token: vscode.CancellationToken
    ): vscode.CompletionItem | Thenable<vscode.CompletionItem> {
        
        // Add additional documentation or modify item if needed
        return item;
    }
}