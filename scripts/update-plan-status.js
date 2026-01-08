#!/usr/bin/env node

/**
 * Plan Status Management Script
 *
 * Manages the status of implementation plans in the index.md file.
 * Supports registering new plans, updating statuses, and generating statistics.
 *
 * Usage:
 *   node scripts/update-plan-status.js --register --file=plan.md --title="Title" --description="Desc" --status=backlog
 *   node scripts/update-plan-status.js --update --file=plan.md --status=in-progress --note="Started work"
 *   node scripts/update-plan-status.js --list
 *   node scripts/update-plan-status.js --help
 */

import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

// Get __dirname equivalent in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Constants
const INDEX_PATH = resolve(__dirname, '../docs/plans/index.md');

const VALID_STATUSES = ['backlog', 'ready', 'in-progress', 'for-review', 'done', 'blocked'];

const STATUS_CONFIG = {
  'backlog': {
    emoji: '🔴',
    label: 'Backlog',
    section: '🔴 Backlog',
    description: 'Not started, planned for future'
  },
  'ready': {
    emoji: '🟢',
    label: 'Ready',
    section: '🟢 Ready',
    description: 'Ready to start implementation'
  },
  'in-progress': {
    emoji: '🟡',
    label: 'In Progress',
    section: '🟡 In Progress',
    description: 'Currently being implemented'
  },
  'for-review': {
    emoji: '🔵',
    label: 'For Review',
    section: '🔵 For Review',
    description: 'Implemented, needs testing/review'
  },
  'done': {
    emoji: '✅',
    label: 'Done',
    section: '✅ Done',
    description: 'Completed and verified'
  },
  'blocked': {
    emoji: '🚫',
    label: 'Blocked',
    section: '🚫 Blocked',
    description: 'Blocked by dependencies or issues'
  }
};

// Helper functions
function getCurrentDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function parseArguments() {
  const args = process.argv.slice(2);
  const parsed = {
    operation: null,
    file: null,
    title: null,
    description: null,
    status: null,
    note: null
  };

  for (const arg of args) {
    if (arg === '--help' || arg === '-h') {
      parsed.operation = 'help';
    } else if (arg === '--register') {
      parsed.operation = 'register';
    } else if (arg === '--update') {
      parsed.operation = 'update';
    } else if (arg === '--list') {
      parsed.operation = 'list';
    } else if (arg.startsWith('--file=')) {
      parsed.file = arg.split('=')[1];
    } else if (arg.startsWith('--title=')) {
      parsed.title = arg.split('=')[1];
    } else if (arg.startsWith('--description=')) {
      parsed.description = arg.split('=')[1];
    } else if (arg.startsWith('--status=')) {
      parsed.status = arg.split('=')[1];
    } else if (arg.startsWith('--note=')) {
      parsed.note = arg.split('=')[1];
    }
  }

  return parsed;
}

function showHelp() {
  console.log(`
Plan Status Management Script
==============================

Usage:
  node scripts/update-plan-status.js [OPERATION] [OPTIONS]

Operations:
  --register          Register a new plan
  --update            Update existing plan status
  --list              List all plans with their statuses
  --help, -h          Show this help message

Options:
  --file=<filename>           Plan filename (required for register/update)
  --title=<title>             Plan title (required for register)
  --description=<desc>        Plan description (required for register)
  --status=<status>           Plan status (required for register/update)
  --note=<note>               Optional note for changelog (update only)

Valid Statuses:
  backlog             Not started, planned for future
  ready               Ready to start implementation
  in-progress         Currently being implemented
  for-review          Implemented, needs testing/review
  done                Completed and verified
  blocked             Blocked by dependencies or issues

Examples:
  # Register new plan as Backlog
  node scripts/update-plan-status.js --register \\
    --file=2026-01-08-auth-module.md \\
    --title="Authentication Module" \\
    --description="User auth system" \\
    --status=backlog

  # Update plan to Ready
  node scripts/update-plan-status.js --update \\
    --file=2026-01-08-auth-module.md \\
    --status=ready \\
    --note="Plan completed, ready to start"

  # Update to In Progress
  node scripts/update-plan-status.js --update \\
    --file=2026-01-08-auth-module.md \\
    --status=in-progress

  # Update to Done
  node scripts/update-plan-status.js --update \\
    --file=2026-01-08-auth-module.md \\
    --status=done \\
    --note="All tasks completed and tested"

  # Mark as Blocked
  node scripts/update-plan-status.js --update \\
    --file=2026-01-08-auth-module.md \\
    --status=blocked \\
    --note="Waiting for API changes"

  # List all plans
  node scripts/update-plan-status.js --list
`);
}

function parseIndex(content) {
  const sections = {
    'done': [],
    'for-review': [],
    'in-progress': [],
    'ready': [],
    'blocked': [],
    'backlog': []
  };

  const lines = content.split('\n');
  let currentSection = null;
  let currentPlan = null;
  let inPlanBlock = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Detect section headers
    if (line.startsWith('## ✅ Done')) {
      currentSection = 'done';
      inPlanBlock = false;
    } else if (line.startsWith('## 🔵 For Review')) {
      currentSection = 'for-review';
      inPlanBlock = false;
    } else if (line.startsWith('## 🟡 In Progress')) {
      currentSection = 'in-progress';
      inPlanBlock = false;
    } else if (line.startsWith('## 🟢 Ready')) {
      currentSection = 'ready';
      inPlanBlock = false;
    } else if (line.startsWith('## 🚫 Blocked')) {
      currentSection = 'blocked';
      inPlanBlock = false;
    } else if (line.startsWith('## 🔴 Backlog')) {
      currentSection = 'backlog';
      inPlanBlock = false;
    } else if (line.startsWith('## ')) {
      currentSection = null;
      inPlanBlock = false;
    }

    // Detect plan headers
    if (currentSection && line.startsWith('### [')) {
      const match = line.match(/^### \[(.+?)\]\(\.\/(.+?)\)$/);
      if (match) {
        const [, title, file] = match;
        currentPlan = {
          title,
          file,
          status: currentSection,
          content: [line],
          startLine: i,
          endLine: i
        };
        inPlanBlock = true;
      }
    } else if (inPlanBlock && currentPlan) {
      // Check if we're starting a new plan or section
      if (line.startsWith('### [') || line.startsWith('## ')) {
        // End current plan
        currentPlan.endLine = i - 1;
        sections[currentSection].push(currentPlan);
        inPlanBlock = false;
        currentPlan = null;

        // Re-process this line
        i--;
      } else if (line.trim() === '---') {
        // End current plan at separator
        currentPlan.content.push(line);
        currentPlan.endLine = i;
        sections[currentSection].push(currentPlan);
        inPlanBlock = false;
        currentPlan = null;
      } else {
        // Add line to current plan content
        currentPlan.content.push(line);
        currentPlan.endLine = i;
      }
    }
  }

  // Add last plan if still in block
  if (inPlanBlock && currentPlan && currentSection) {
    sections[currentSection].push(currentPlan);
  }

  return { sections, lines };
}

function findPlan(sections, filename) {
  for (const [status, plans] of Object.entries(sections)) {
    const plan = plans.find(p => p.file === filename);
    if (plan) {
      return { plan, status };
    }
  }
  return { plan: null, status: null };
}

function formatPlanBlock(title, file, description, status, note = null) {
  const config = STATUS_CONFIG[status];
  let block = `### [${title}](./${file})\n`;
  block += `**Status:** ${config.emoji} ${config.label}\n`;
  block += `**Description:** ${description}\n`;

  if (note) {
    block += `**Notes:** ${note}\n`;
  }

  return block;
}

function recalculateStats(sections) {
  const counts = {
    done: sections.done.length,
    'for-review': sections['for-review'].length,
    'in-progress': sections['in-progress'].length,
    ready: sections.ready.length,
    blocked: sections.blocked.length,
    backlog: sections.backlog.length
  };

  const total = Object.values(counts).reduce((sum, count) => sum + count, 0);

  const stats = [];
  stats.push(`| Status | Count | Percentage |`);
  stats.push(`|--------|-------|------------|`);

  for (const [status, count] of Object.entries(counts)) {
    if (count > 0) {
      const config = STATUS_CONFIG[status];
      const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
      stats.push(`| ${config.emoji} ${config.label} | ${count} | ${percentage}% |`);
    }
  }

  return stats.join('\n');
}

function updateIndex(content, sections, updatedSections = null) {
  const lines = content.split('\n');
  let result = [];
  let i = 0;

  const sectionsToUse = updatedSections || sections;
  const sectionOrder = ['done', 'for-review', 'in-progress', 'ready', 'blocked', 'backlog'];
  const processedSections = new Set();

  // Helper to render a section
  function renderSection(statusKey) {
    const config = STATUS_CONFIG[statusKey];
    const plans = sectionsToUse[statusKey];

    if (plans.length > 0) {
      result.push(`## ${config.section}`);
      result.push('');

      for (const plan of plans) {
        result.push(...plan.content);
        result.push('');
      }
      result.push('---');
      result.push('');
    }
  }

  while (i < lines.length) {
    const line = lines[i];

    // Update "Last Updated" date
    if (line.startsWith('**Last Updated:**')) {
      result.push(`**Last Updated:** ${getCurrentDate()}`);
      i++;
      continue;
    }

    // Update statistics section
    if (line === '## 📊 Summary Statistics') {
      result.push(line);
      result.push('');

      // Skip old stats table
      i++;
      while (i < lines.length && !lines[i].startsWith('##') && !lines[i].startsWith('###')) {
        i++;
      }

      // Add new stats
      result.push(recalculateStats(sectionsToUse));
      result.push('');
      continue;
    }

    // Check if this is a status section header
    const sectionMatch = sectionOrder.find(statusKey => {
      const config = STATUS_CONFIG[statusKey];
      return line.startsWith(`## ${config.section.split(' ')[0]}`);
    });

    if (sectionMatch) {
      // Skip old content for this section
      i++;
      while (i < lines.length && !lines[i].startsWith('## ')) {
        i++;
      }

      // Render this section and all subsequent sections in order
      for (const statusKey of sectionOrder) {
        if (!processedSections.has(statusKey)) {
          renderSection(statusKey);
          processedSections.add(statusKey);
        }
      }
      continue;
    }

    result.push(line);
    i++;
  }

  // If we haven't processed sections yet (shouldn't happen), add them at the end
  if (processedSections.size === 0) {
    result.push('');
    for (const statusKey of sectionOrder) {
      renderSection(statusKey);
    }
  }

  return result.join('\n');
}

function appendChangelog(content, message) {
  const lines = content.split('\n');
  const changelogIndex = lines.findIndex(line => line === '## 📝 Change Log');

  if (changelogIndex === -1) {
    console.error('Warning: Could not find Change Log section');
    return content;
  }

  // Find the first date header after Change Log
  let insertIndex = changelogIndex + 2;
  const currentDate = getCurrentDate();
  const dateHeader = `### ${currentDate}`;

  // Check if today's date already exists
  let dateHeaderIndex = -1;
  for (let i = changelogIndex; i < lines.length; i++) {
    if (lines[i] === dateHeader) {
      dateHeaderIndex = i;
      break;
    }
    if (lines[i].startsWith('### ') && lines[i] !== dateHeader) {
      insertIndex = i;
      break;
    }
  }

  if (dateHeaderIndex !== -1) {
    // Add to existing date section
    lines.splice(dateHeaderIndex + 1, 0, `- ${message}`);
  } else {
    // Create new date section
    lines.splice(insertIndex, 0, dateHeader);
    lines.splice(insertIndex + 1, 0, `- ${message}`);
    lines.splice(insertIndex + 2, 0, '');
  }

  return lines.join('\n');
}

function registerPlan(args) {
  // Validate arguments
  if (!args.file) {
    console.error('Error: --file is required for registration');
    process.exit(1);
  }
  if (!args.title) {
    console.error('Error: --title is required for registration');
    process.exit(1);
  }
  if (!args.description) {
    console.error('Error: --description is required for registration');
    process.exit(1);
  }
  if (!args.status) {
    console.error('Error: --status is required for registration');
    process.exit(1);
  }
  if (!VALID_STATUSES.includes(args.status)) {
    console.error(`Error: Invalid status '${args.status}'. Valid statuses: ${VALID_STATUSES.join(', ')}`);
    process.exit(1);
  }

  // Read and parse index
  const content = readFileSync(INDEX_PATH, 'utf-8');
  const { sections } = parseIndex(content);

  // Check if plan already exists
  const { plan: existingPlan } = findPlan(sections, args.file);
  if (existingPlan) {
    console.warn(`Warning: Plan '${args.file}' already exists with status '${existingPlan.status}'`);
    console.log('Use --update to change its status');
    return;
  }

  // Create new plan
  const newPlan = {
    title: args.title,
    file: args.file,
    status: args.status,
    content: formatPlanBlock(args.title, args.file, args.description, args.status).split('\n')
  };

  sections[args.status].push(newPlan);

  // Update index
  let updatedContent = updateIndex(content, sections, sections);

  // Add changelog entry
  const config = STATUS_CONFIG[args.status];
  updatedContent = appendChangelog(
    updatedContent,
    `${config.emoji} Registered new plan: [${args.title}](./${args.file}) as ${config.label}`
  );

  // Write back
  writeFileSync(INDEX_PATH, updatedContent, 'utf-8');

  console.log(`✅ Successfully registered plan '${args.title}' (${args.file}) with status '${args.status}'`);
}

function updatePlanStatus(args) {
  // Validate arguments
  if (!args.file) {
    console.error('Error: --file is required for update');
    process.exit(1);
  }
  if (!args.status) {
    console.error('Error: --status is required for update');
    process.exit(1);
  }
  if (!VALID_STATUSES.includes(args.status)) {
    console.error(`Error: Invalid status '${args.status}'. Valid statuses: ${VALID_STATUSES.join(', ')}`);
    process.exit(1);
  }

  // Read and parse index
  const content = readFileSync(INDEX_PATH, 'utf-8');
  const { sections } = parseIndex(content);

  // Find plan
  const { plan, status: currentStatus } = findPlan(sections, args.file);
  if (!plan) {
    console.error(`Error: Plan '${args.file}' not found`);
    process.exit(1);
  }

  if (currentStatus === args.status) {
    console.log(`Plan '${args.file}' is already in status '${args.status}'`);
    return;
  }

  // Remove from current section
  sections[currentStatus] = sections[currentStatus].filter(p => p.file !== args.file);

  // Update plan status
  plan.status = args.status;

  // Update status line in content
  const config = STATUS_CONFIG[args.status];
  for (let i = 0; i < plan.content.length; i++) {
    if (plan.content[i].startsWith('**Status:**')) {
      plan.content[i] = `**Status:** ${config.emoji} ${config.label}`;
      break;
    }
  }

  // Add note if provided
  if (args.note) {
    let noteAdded = false;
    for (let i = 0; i < plan.content.length; i++) {
      if (plan.content[i].startsWith('**Notes:**')) {
        plan.content[i] = `**Notes:** ${args.note}`;
        noteAdded = true;
        break;
      }
    }
    if (!noteAdded) {
      // Find where to insert (after Description)
      for (let i = 0; i < plan.content.length; i++) {
        if (plan.content[i].startsWith('**Description:**')) {
          plan.content.splice(i + 1, 0, `**Notes:** ${args.note}`);
          break;
        }
      }
    }
  }

  // Add to new section
  sections[args.status].push(plan);

  // Update index
  let updatedContent = updateIndex(content, sections, sections);

  // Add changelog entry
  const oldConfig = STATUS_CONFIG[currentStatus];
  const changelogMessage = args.note
    ? `${config.emoji} Updated [${plan.title}](./${plan.file}): ${oldConfig.label} → ${config.label} - ${args.note}`
    : `${config.emoji} Updated [${plan.title}](./${plan.file}): ${oldConfig.label} → ${config.label}`;

  updatedContent = appendChangelog(updatedContent, changelogMessage);

  // Write back
  writeFileSync(INDEX_PATH, updatedContent, 'utf-8');

  console.log(`✅ Successfully updated plan '${plan.title}' (${args.file})`);
  console.log(`   Status changed: ${oldConfig.emoji} ${oldConfig.label} → ${config.emoji} ${config.label}`);
  if (args.note) {
    console.log(`   Note: ${args.note}`);
  }
}

function listPlans() {
  // Read and parse index
  const content = readFileSync(INDEX_PATH, 'utf-8');
  const { sections } = parseIndex(content);

  console.log('\n📋 All Plans\n');
  console.log('='.repeat(80));

  let totalCount = 0;

  for (const statusKey of ['done', 'for-review', 'in-progress', 'ready', 'blocked', 'backlog']) {
    const plans = sections[statusKey];
    if (plans.length > 0) {
      const config = STATUS_CONFIG[statusKey];
      console.log(`\n${config.emoji} ${config.label} (${plans.length})`);
      console.log('-'.repeat(80));

      for (const plan of plans) {
        console.log(`  • ${plan.title}`);
        console.log(`    File: ${plan.file}`);
        totalCount++;
      }
    }
  }

  console.log('\n' + '='.repeat(80));
  console.log(`Total Plans: ${totalCount}\n`);
}

// Main execution
function main() {
  const args = parseArguments();

  if (!args.operation || args.operation === 'help') {
    showHelp();
    process.exit(0);
  }

  try {
    switch (args.operation) {
      case 'register':
        registerPlan(args);
        break;
      case 'update':
        updatePlanStatus(args);
        break;
      case 'list':
        listPlans();
        break;
      default:
        console.error(`Error: Unknown operation '${args.operation}'`);
        showHelp();
        process.exit(1);
    }
  } catch (error) {
    console.error(`Error: ${error.message}`);
    if (process.env.DEBUG) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

main();
