VS CODE EXTENSION ANALYSIS SUMMARY
========================================

FILES ANALYZED: 102

FILE CATEGORIES:
----------------
- codeActions.ts: 1 files
- dashboard.ts: 1 files
- diagnostics.ts: 1 files
- extension.ts: 1 files
- simple-extension.ts: 1 files
- statusBar.ts: 1 files
-  treeView.ts: 1 files
-     commands: 1 files
-         core: 1 files
-     features: 6 files
-    providers: 9 files
-     services: 6 files
-         test: 1 files
-        types: 1 files
-           ui: 2 files
-        utils: 4 files
-         root: 38 files
-       config: 1 files
-        build: 25 files

IMPORT ANALYSIS:
----------------
-     internal: 170 imports
-   vscode-api: 92 imports
-     external: 34 imports
- node-builtin: 58 imports

PACKAGE DEPENDENCIES:
--------------------
- Production: 0 dependencies
- Development: 13 dependencies
- Total: 13 dependencies

VS CODE EXTENSION - MODULE COUPLING MATRIX
==================================================
      Source |    build codeActi commands   config     core dashboar diagnost extensio 
--------------------------------------------------------------------------------------
       build |       --                                                                
codeActions.ts |        1       --        1        1        1        1        1        1 
    commands |        8        8       --        8        8        8        8        8 
      config |                                  --                                     
        core |       15       15       15       15       --       15       15       15 
dashboard.ts |        1        1        1        1        1       --        1        1 
diagnostics.ts |                                                             --          
extension.ts |       11       11       11       11       11       11       11       -- 
