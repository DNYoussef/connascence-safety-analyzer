import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { ConfigurationService } from '../services/configurationService';
import { ExtensionLogger } from '../utils/logger';

/**
 * Tree item for markdown files and directories
 */
export class MarkdownTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly resourceUri?: vscode.Uri,
        public readonly isMarkdownFile?: boolean,
        public readonly contextValue?: string
    ) {
        super(label, collapsibleState);
        
        if (resourceUri) {
            this.resourceUri = resourceUri;
            this.tooltip = resourceUri.fsPath;
            
            if (isMarkdownFile) {
                this.command = {
                    command: 'connascence.openMarkdownFile',
                    title: 'Open Markdown File',
                    arguments: [resourceUri]
                };
                this.iconPath = new vscode.ThemeIcon('markdown');
                this.contextValue = 'markdownFile';
            } else {
                this.iconPath = vscode.ThemeIcon.Folder;
                this.contextValue = 'markdownFolder';
            }
        }
    }
}

/**
 * Markdown Table of Contents Provider
 * 
 * Creates a sidebar tree view showing all markdown files in the workspace
 * organized by directory structure with click-to-open functionality
 */
export class MarkdownTableOfContentsProvider implements vscode.TreeDataProvider<MarkdownTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<MarkdownTreeItem | undefined | null | void> = new vscode.EventEmitter<MarkdownTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<MarkdownTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private disposables: vscode.Disposable[] = [];
    private markdownFiles: Map<string, vscode.Uri[]> = new Map();
    private fileWatcher: vscode.FileSystemWatcher | undefined;

    constructor(
        private context: vscode.ExtensionContext,
        private configService: ConfigurationService,
        private logger: ExtensionLogger
    ) {
        this.setupFileWatcher();
        this.registerCommands();
        this.refresh();
    }

    /**
     * Refresh the tree view
     */
    public refresh(): void {
        this.scanWorkspaceForMarkdownFiles();
        this._onDidChangeTreeData.fire();
    }

    /**
     * Get tree item representation
     */
    getTreeItem(element: MarkdownTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * Get children of a tree item
     */
    getChildren(element?: MarkdownTreeItem): Thenable<MarkdownTreeItem[]> {
        if (!element) {
            // Root level - show workspace folders and markdown files
            return Promise.resolve(this.getRootItems());
        } else {
            // Directory level - show subdirectories and markdown files
            return Promise.resolve(this.getDirectoryChildren(element));
        }
    }

    // === PRIVATE METHODS ===

    private setupFileWatcher(): void {
        // Watch for markdown file changes
        this.fileWatcher = vscode.workspace.createFileSystemWatcher('**/*.{md,markdown,mdx}', false, false, false);
        
        this.fileWatcher.onDidCreate(() => {
            this.refresh();
        });
        
        this.fileWatcher.onDidDelete(() => {
            this.refresh();
        });
        
        this.fileWatcher.onDidChange(() => {
            // Don't refresh on content changes, only on file system changes
        });
        
        this.disposables.push(this.fileWatcher);
    }

    private registerCommands(): void {
        // Open markdown file command
        this.disposables.push(
            vscode.commands.registerCommand('connascence.openMarkdownFile', (uri: vscode.Uri) => {
                this.openMarkdownFile(uri);
            })
        );

        // Refresh command
        this.disposables.push(
            vscode.commands.registerCommand('connascence.refreshMarkdownTOC', () => {
                this.refresh();
                vscode.window.showInformationMessage('Markdown Table of Contents refreshed');
            })
        );

        // Create new markdown file command
        this.disposables.push(
            vscode.commands.registerCommand('connascence.createMarkdownFile', async (folder?: vscode.Uri) => {
                await this.createNewMarkdownFile(folder);
            })
        );

        // Open in preview command  
        this.disposables.push(
            vscode.commands.registerCommand('connascence.openMarkdownPreview', (uri: vscode.Uri) => {
                vscode.commands.executeCommand('markdown.showPreview', uri);
            })
        );

        this.logger.info('Markdown TOC: Registered commands');
    }

    private async scanWorkspaceForMarkdownFiles(): Promise<void> {
        this.markdownFiles.clear();
        
        if (!vscode.workspace.workspaceFolders) {
            return;
        }

        for (const workspaceFolder of vscode.workspace.workspaceFolders) {
            try {
                // Use glob pattern to find all markdown files
                const pattern = new vscode.RelativePattern(workspaceFolder, '**/*.{md,markdown,mdx}');
                const files = await vscode.workspace.findFiles(pattern, '**/node_modules/**');
                
                // Group files by directory
                const directoryMap = new Map<string, vscode.Uri[]>();
                
                for (const file of files) {
                    const relativePath = vscode.workspace.asRelativePath(file, false);
                    const directory = path.dirname(relativePath);
                    
                    if (!directoryMap.has(directory)) {
                        directoryMap.set(directory, []);
                    }
                    directoryMap.get(directory)!.push(file);
                }
                
                // Sort files within each directory
                for (const [dir, files] of directoryMap) {
                    files.sort((a, b) => {
                        const nameA = path.basename(a.fsPath).toLowerCase();
                        const nameB = path.basename(b.fsPath).toLowerCase();
                        
                        // README files first
                        if (nameA.startsWith('readme') && !nameB.startsWith('readme')) return -1;
                        if (!nameA.startsWith('readme') && nameB.startsWith('readme')) return 1;
                        
                        return nameA.localeCompare(nameB);
                    });
                    
                    this.markdownFiles.set(dir, files);
                }
                
            } catch (error) {
                this.logger.error('Failed to scan workspace for markdown files', error);
            }
        }
    }

    private getRootItems(): MarkdownTreeItem[] {
        const items: MarkdownTreeItem[] = [];
        const processedDirectories = new Set<string>();

        // Sort directories for consistent display
        const sortedDirectories = Array.from(this.markdownFiles.keys()).sort((a, b) => {
            // Root files first
            if (a === '.' && b !== '.') return -1;
            if (a !== '.' && b === '.') return 1;
            return a.localeCompare(b);
        });

        for (const directory of sortedDirectories) {
            const files = this.markdownFiles.get(directory) || [];
            
            if (directory === '.') {
                // Root level files - add directly
                for (const file of files) {
                    const fileName = path.basename(file.fsPath);
                    const item = new MarkdownTreeItem(
                        this.getDisplayName(fileName),
                        vscode.TreeItemCollapsibleState.None,
                        file,
                        true,
                        'markdownFile'
                    );
                    items.push(item);
                }
            } else {
                // Create directory structure
                const parts = directory.split(path.sep);
                let currentPath = '';
                
                for (let i = 0; i < parts.length; i++) {
                    currentPath = i === 0 ? parts[i] : path.join(currentPath, parts[i]);
                    
                    if (!processedDirectories.has(currentPath)) {
                        processedDirectories.add(currentPath);
                        
                        // Only create top-level directories here
                        if (i === 0) {
                            const directoryUri = vscode.Uri.joinPath(vscode.workspace.workspaceFolders![0].uri, currentPath);
                            const item = new MarkdownTreeItem(
                                parts[i],
                                vscode.TreeItemCollapsibleState.Collapsed,
                                directoryUri,
                                false,
                                'markdownFolder'
                            );
                            items.push(item);
                        }
                    }
                }
            }
        }

        // Add summary at the top if there are files
        const totalFiles = Array.from(this.markdownFiles.values()).reduce((sum, files) => sum + files.length, 0);
        if (totalFiles > 0) {
            const summaryItem = new MarkdownTreeItem(
                `📚 ${totalFiles} Markdown Files`,
                vscode.TreeItemCollapsibleState.None,
                undefined,
                false,
                'summary'
            );
            summaryItem.iconPath = new vscode.ThemeIcon('book');
            summaryItem.tooltip = `Total markdown files found: ${totalFiles}`;
            items.unshift(summaryItem);
        }

        return items;
    }

    private getDirectoryChildren(element: MarkdownTreeItem): MarkdownTreeItem[] {
        if (!element.resourceUri) {
            return [];
        }

        const items: MarkdownTreeItem[] = [];
        const elementPath = vscode.workspace.asRelativePath(element.resourceUri, false);
        
        // Find subdirectories and files for this directory
        const childDirectories = new Set<string>();
        const directFiles: vscode.Uri[] = [];
        
        for (const [directory, files] of this.markdownFiles) {
            if (directory.startsWith(elementPath) && directory !== elementPath) {
                const relativePath = path.relative(elementPath, directory);
                const firstPart = relativePath.split(path.sep)[0];
                
                if (!firstPart.includes(path.sep)) {
                    childDirectories.add(firstPart);
                }
            } else if (directory === elementPath) {
                directFiles.push(...files);
            }
        }
        
        // Add subdirectories
        const sortedDirectories = Array.from(childDirectories).sort();
        for (const dirName of sortedDirectories) {
            const dirUri = vscode.Uri.joinPath(element.resourceUri, dirName);
            const item = new MarkdownTreeItem(
                dirName,
                vscode.TreeItemCollapsibleState.Collapsed,
                dirUri,
                false,
                'markdownFolder'
            );
            items.push(item);
        }
        
        // Add files in this directory
        for (const file of directFiles) {
            const fileName = path.basename(file.fsPath);
            const item = new MarkdownTreeItem(
                this.getDisplayName(fileName),
                vscode.TreeItemCollapsibleState.None,
                file,
                true,
                'markdownFile'
            );
            items.push(item);
        }
        
        return items;
    }

    private getDisplayName(fileName: string): string {
        // Remove extension and format display name
        const nameWithoutExt = path.parse(fileName).name;
        
        // Special formatting for common file names
        if (nameWithoutExt.toLowerCase() === 'readme') {
            return '📖 README';
        }
        
        if (nameWithoutExt.toLowerCase() === 'changelog') {
            return '📝 CHANGELOG';
        }
        
        if (nameWithoutExt.toLowerCase() === 'license') {
            return '⚖️ LICENSE';
        }
        
        if (nameWithoutExt.toLowerCase() === 'contributing') {
            return '🤝 CONTRIBUTING';
        }

        // Format other names: capitalize words and replace dashes/underscores
        return nameWithoutExt
            .replace(/[-_]/g, ' ')
            .replace(/\b\w/g, char => char.toUpperCase());
    }

    private async openMarkdownFile(uri: vscode.Uri): Promise<void> {
        try {
            // Check if file exists
            await vscode.workspace.fs.stat(uri);
            
            // Open in editor
            const document = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(document, {
                preview: false,
                preserveFocus: false
            });
            
            this.logger.info(`Opened markdown file: ${uri.fsPath}`);
            
        } catch (error) {
            this.logger.error(`Failed to open markdown file: ${uri.fsPath}`, error);
            vscode.window.showErrorMessage(`Failed to open file: ${path.basename(uri.fsPath)}`);
        }
    }

    private async createNewMarkdownFile(folder?: vscode.Uri): Promise<void> {
        try {
            const fileName = await vscode.window.showInputBox({
                prompt: 'Enter markdown file name',
                placeHolder: 'my-document.md',
                validateInput: (value) => {
                    if (!value) return 'File name is required';
                    if (!value.endsWith('.md') && !value.endsWith('.markdown')) {
                        return 'File must have .md or .markdown extension';
                    }
                    return null;
                }
            });
            
            if (!fileName) return;
            
            const targetFolder = folder || vscode.workspace.workspaceFolders?.[0]?.uri;
            if (!targetFolder) {
                vscode.window.showErrorMessage('No workspace folder available');
                return;
            }
            
            const fileUri = vscode.Uri.joinPath(targetFolder, fileName);
            
            // Create file with basic content
            const basicContent = `# ${path.parse(fileName).name.replace(/[-_]/g, ' ')}\n\n<!-- Add your content here -->\n`;
            
            await vscode.workspace.fs.writeFile(fileUri, Buffer.from(basicContent, 'utf8'));
            
            // Open the new file
            await this.openMarkdownFile(fileUri);
            
            vscode.window.showInformationMessage(`Created markdown file: ${fileName}`);
            
        } catch (error) {
            this.logger.error('Failed to create new markdown file', error);
            vscode.window.showErrorMessage('Failed to create markdown file');
        }
    }

    public dispose(): void {
        this._onDidChangeTreeData.dispose();
        this.fileWatcher?.dispose();
        
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
    }
}