/**
 * Distill CGYSO Articles into Concise Guides
 *
 * This script reads the downloaded CGYSO articles and extracts key insights
 * to create shorter, focused guides that can be used by LLMs.
 *
 * Usage: npx tsx scripts/distill-cgyso-articles.ts
 */

import * as fs from 'fs';
import * as path from 'path';

const ARTICLES_DIR = path.join(__dirname, '../data/cgyso-articles');
const OUTPUT_DIR = path.join(__dirname, '../data/cgyso-guides');

interface Article {
  title: string;
  content: string;
  category: string;
  filename: string;
}

interface DistilledGuide {
  topic: string;
  summary: string;
  keyPoints: string[];
  recommendations: string[];
  synergies?: string[];
}

// Read all articles from a category
function readCategoryArticles(category: string): Article[] {
  const categoryDir = path.join(ARTICLES_DIR, category);
  if (!fs.existsSync(categoryDir)) {
    return [];
  }

  const files = fs.readdirSync(categoryDir).filter(f => f.endsWith('.md'));
  const articles: Article[] = [];

  for (const file of files) {
    const content = fs.readFileSync(path.join(categoryDir, file), 'utf-8');
    const title = content.match(/^# (.+)$/m)?.[1] || file.replace('.md', '');
    articles.push({
      title,
      content,
      category,
      filename: file,
    });
  }

  return articles;
}

// Extract bullet points from markdown content
function extractBulletPoints(content: string): string[] {
  const points: string[] = [];
  const lines = content.split('\n');

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const point = trimmed.slice(2).trim();
      if (point.length > 20 && point.length < 500) {
        points.push(point);
      }
    }
  }

  return points;
}

// Extract key insights from commander articles
function distillCommanderArticle(article: Article): DistilledGuide | null {
  const content = article.content;

  // Skip if too short
  if (content.length < 500) {
    return null;
  }

  // Extract commander name from title
  const commanderMatch = article.title.match(/(?:Imperial|Rebel|Republic|Separatist)?\s*[Cc]ommander[:\s]+(.+)|(.+?)(?:\s*-?\s*(?:Know Your Enemy|Commander Review))/i);
  const topic = commanderMatch?.[1] || commanderMatch?.[2] || article.title;

  // Extract bullet points
  const bulletPoints = extractBulletPoints(content);

  // Look for key patterns
  const recommendations: string[] = [];
  const synergies: string[] = [];

  for (const point of bulletPoints) {
    const pointLower = point.toLowerCase();

    // Look for synergy mentions
    if (pointLower.includes('synerg') || pointLower.includes('works well') ||
        pointLower.includes('pairs') || pointLower.includes('combo') ||
        pointLower.includes('great with') || pointLower.includes('combine')) {
      synergies.push(point);
    }

    // Look for recommendations
    if (pointLower.includes('recommend') || pointLower.includes('should') ||
        pointLower.includes('best') || pointLower.includes('want to') ||
        pointLower.includes('great option') || pointLower.includes('strong')) {
      recommendations.push(point);
    }
  }

  // Create a summary from the first paragraph after the metadata
  const contentAfterMeta = content.split('---')[1] || content;
  const firstParagraph = contentAfterMeta
    .split('\n\n')
    .find(p => p.length > 100 && !p.startsWith('#') && !p.startsWith('-'));
  const summary = firstParagraph?.slice(0, 300).trim() || '';

  return {
    topic,
    summary,
    keyPoints: bulletPoints.slice(0, 10), // Top 10 points
    recommendations: recommendations.slice(0, 5),
    synergies: synergies.slice(0, 5),
  };
}

// Generate markdown guide from distilled content
function generateGuideMarkdown(guides: DistilledGuide[], category: string): string {
  let markdown = `# ${category.charAt(0).toUpperCase() + category.slice(1)} Guide\n\n`;
  markdown += `*Distilled from Cannot Get Your Ship Out articles*\n\n`;
  markdown += `---\n\n`;

  for (const guide of guides) {
    markdown += `## ${guide.topic}\n\n`;

    if (guide.summary) {
      markdown += `${guide.summary}\n\n`;
    }

    if (guide.keyPoints.length > 0) {
      markdown += `### Key Points\n`;
      for (const point of guide.keyPoints) {
        markdown += `- ${point}\n`;
      }
      markdown += '\n';
    }

    if (guide.recommendations && guide.recommendations.length > 0) {
      markdown += `### Recommendations\n`;
      for (const rec of guide.recommendations) {
        markdown += `- ${rec}\n`;
      }
      markdown += '\n';
    }

    if (guide.synergies && guide.synergies.length > 0) {
      markdown += `### Synergies\n`;
      for (const syn of guide.synergies) {
        markdown += `- ${syn}\n`;
      }
      markdown += '\n';
    }

    markdown += `---\n\n`;
  }

  return markdown;
}

// Create a compact JSON format for model consumption
function createModelGuide(guides: DistilledGuide[]): object[] {
  return guides.map(g => ({
    name: g.topic,
    summary: g.summary.slice(0, 200),
    tips: g.keyPoints.slice(0, 5),
    synergies: g.synergies?.slice(0, 3) || [],
  }));
}

async function main() {
  console.log('========================================');
  console.log('  CGYSO Article Distiller');
  console.log('========================================\n');

  // Create output directory
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // Process each category
  const categories = ['commanders', 'ships', 'squadrons', 'upgrades', 'tactics', 'fleet-building'];

  for (const category of categories) {
    console.log(`\nProcessing ${category}...`);
    const articles = readCategoryArticles(category);
    console.log(`  Found ${articles.length} articles`);

    const guides: DistilledGuide[] = [];

    for (const article of articles) {
      const guide = distillCommanderArticle(article);
      if (guide && guide.keyPoints.length > 0) {
        guides.push(guide);
      }
    }

    console.log(`  Distilled ${guides.length} guides`);

    if (guides.length > 0) {
      // Save markdown guide
      const markdown = generateGuideMarkdown(guides, category);
      fs.writeFileSync(path.join(OUTPUT_DIR, `${category}-guide.md`), markdown);

      // Save compact JSON for models
      const modelGuide = createModelGuide(guides);
      fs.writeFileSync(
        path.join(OUTPUT_DIR, `${category}-guide.json`),
        JSON.stringify(modelGuide, null, 2)
      );

      console.log(`  ✓ Saved: ${category}-guide.md`);
      console.log(`  ✓ Saved: ${category}-guide.json`);
    }
  }

  // Create a combined guide index
  const indexContent = categories.map(cat => {
    const jsonPath = path.join(OUTPUT_DIR, `${cat}-guide.json`);
    if (fs.existsSync(jsonPath)) {
      return {
        category: cat,
        guides: JSON.parse(fs.readFileSync(jsonPath, 'utf-8')),
      };
    }
    return null;
  }).filter(Boolean);

  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'all-guides.json'),
    JSON.stringify(indexContent, null, 2)
  );

  console.log('\n========================================');
  console.log('  Distillation Complete!');
  console.log('========================================');
  console.log(`\nGuides saved to: ${OUTPUT_DIR}`);
}

main().catch(console.error);
