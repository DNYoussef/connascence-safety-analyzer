const fs = require('fs');
const path = require('path');

// Agent directories to process
const agentDirs = [
  'C:\\Users\\17175\\.claude\\agents',
  'C:\\Users\\17175\\Desktop\\connascence\\.claude\\agents'
];

// Counter for tracking fixes
let filesProcessed = 0;
let filesFixed = 0;
let errors = [];

// Function to check if file has frontmatter
function hasFrontmatter(content) {
  return content.trimStart().startsWith('---');
}

// Function to extract name from filename
function extractNameFromFile(filePath) {
  const basename = path.basename(filePath, '.md');
  // Convert filename to kebab-case name
  return basename.toLowerCase().replace(/[\s_]/g, '-');
}

// Function to extract description from first heading or paragraph
function extractDescription(content) {
  // Remove existing frontmatter if any
  let cleaned = content.replace(/^---[\s\S]*?---\n/, '');

  // Try to find first heading after title
  const headingMatch = cleaned.match(/^#{1,3}\s+(.+)$/m);
  if (headingMatch && !headingMatch[1].toLowerCase().includes('agent')) {
    return headingMatch[1].trim();
  }

  // Try to find first paragraph
  const paragraphMatch = cleaned.match(/^[A-Z][^\n]{20,150}[.!?]$/m);
  if (paragraphMatch) {
    return paragraphMatch[0].trim();
  }

  // Default description
  return 'Specialized agent for task execution';
}

// Function to add frontmatter to file
function addFrontmatter(filePath, content) {
  const name = extractNameFromFile(filePath);
  const description = extractDescription(content);

  const frontmatter = `---
name: ${name}
description: ${description}
---

`;

  return frontmatter + content;
}

// Function to process a single file
function processFile(filePath) {
  try {
    filesProcessed++;

    // Read file content
    const content = fs.readFileSync(filePath, 'utf8');

    // Check if frontmatter exists
    if (hasFrontmatter(content)) {
      // Check if name field exists
      const nameMatch = content.match(/^---[\s\S]*?name:\s*(.+)$/m);
      if (nameMatch) {
        console.log(`  \\u2713 ${path.basename(filePath)} - Already has name field`);
        return;
      }
    }

    // Add frontmatter
    const updatedContent = addFrontmatter(filePath, content);

    // Write back to file
    fs.writeFileSync(filePath, updatedContent, 'utf8');

    filesFixed++;
    console.log(`  \\u2713 Fixed: ${path.basename(filePath)}`);

  } catch (error) {
    errors.push({ file: filePath, error: error.message });
    console.error(`  \\u2717 Error processing ${path.basename(filePath)}: ${error.message}`);
  }
}

// Function to recursively find all .md files
function findMarkdownFiles(dir, files = []) {
  try {
    if (!fs.existsSync(dir)) {
      console.log(`  ! Directory does not exist: ${dir}`);
      return files;
    }

    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        findMarkdownFiles(fullPath, files);
      } else if (entry.isFile() && entry.name.endsWith('.md')) {
        files.push(fullPath);
      }
    }
  } catch (error) {
    console.error(`  \\u2717 Error reading directory ${dir}: ${error.message}`);
  }

  return files;
}

// Main execution
console.log('Starting agent frontmatter fix...\n');

for (const agentDir of agentDirs) {
  console.log(`Processing directory: ${agentDir}`);

  const mdFiles = findMarkdownFiles(agentDir);
  console.log(`  Found ${mdFiles.length} markdown files\n`);

  for (const file of mdFiles) {
    processFile(file);
  }

  console.log('');
}

// Summary
console.log('==========================================');
console.log('Summary:');
console.log(`  Files processed: ${filesProcessed}`);
console.log(`  Files fixed: ${filesFixed}`);
console.log(`  Errors: ${errors.length}`);

if (errors.length > 0) {
  console.log('\nErrors encountered:');
  errors.forEach(({ file, error }) => {
    console.log(`  - ${path.basename(file)}: ${error}`);
  });
}

console.log('==========================================');
console.log('Done!');
