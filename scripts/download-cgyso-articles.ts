/**
 * Download and catalog articles from "Cannot Get Your Ship Out" blog
 * https://cannotgetyourshipout.blogspot.com/
 *
 * This script:
 * 1. Fetches the sitemap/archive to find all articles
 * 2. Downloads each article's content
 * 3. Categorizes articles by topic (commanders, ships, upgrades, tactics)
 * 4. Saves them in a structured format for later processing
 *
 * Usage: npx tsx scripts/download-cgyso-articles.ts
 */

import * as fs from 'fs';
import * as path from 'path';
import * as cheerio from 'cheerio';

const BLOG_URL = 'https://cannotgetyourshipout.blogspot.com';
const OUTPUT_DIR = path.join(__dirname, '../data/cgyso-articles');

interface Article {
  title: string;
  url: string;
  date: string;
  content: string;
  category: string;
  tags: string[];
}

interface ArticleIndex {
  downloadedAt: string;
  totalArticles: number;
  categories: Record<string, number>;
  articles: Array<{
    title: string;
    url: string;
    date: string;
    category: string;
    filename: string;
  }>;
}

// Rate limiting to be respectful to the server
async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchPage(url: string): Promise<string> {
  console.log(`  Fetching: ${url}`);
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'ArmadaBench-ArticleCrawler/1.0 (Educational research for Star Wars Armada fleet building)',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status}`);
  }

  return response.text();
}

// Categorize article based on title and content
function categorizeArticle(title: string, content: string): { category: string; tags: string[] } {
  const titleLower = title.toLowerCase();
  const contentLower = content.toLowerCase();
  const tags: string[] = [];
  let category = 'general';

  // Commander articles
  if (titleLower.includes('commander') || titleLower.match(/admiral|general|moff|thrawn|ackbar|sloane|vader|rieekan/i)) {
    category = 'commanders';

    // Extract commander name
    const commanderMatch = title.match(/(Admiral|General|Moff|Grand)?\s*([A-Z][a-z]+(\s+[A-Z][a-z]+)?)/);
    if (commanderMatch) tags.push(commanderMatch[0].trim());
  }

  // Ship articles
  else if (titleLower.match(/star destroyer|mc80|victory|nebulon|cr90|corvette|frigate|cruiser|carrier|dreadnought/)) {
    category = 'ships';

    // Check faction
    if (contentLower.includes('rebel') || contentLower.includes('alliance')) tags.push('rebel');
    if (contentLower.includes('imperial') || contentLower.includes('empire')) tags.push('empire');
    if (contentLower.includes('republic')) tags.push('republic');
    if (contentLower.includes('separatist') || contentLower.includes('cis')) tags.push('separatist');
  }

  // Squadron articles
  else if (titleLower.match(/squadron|fighter|bomber|interceptor|x-wing|tie|a-wing|b-wing/)) {
    category = 'squadrons';
  }

  // Upgrade articles
  else if (titleLower.match(/upgrade|title|officer|turbolaser|ordnance|retrofit/)) {
    category = 'upgrades';
  }

  // Tactics/strategy articles
  else if (titleLower.match(/tactic|strategy|guide|how to|basics|advanced|objective|deployment|navigation/)) {
    category = 'tactics';
  }

  // Fleet building
  else if (titleLower.match(/fleet|list|build|400|point/)) {
    category = 'fleet-building';
  }

  // Faction tags
  if (titleLower.includes('rebel') || titleLower.includes('alliance')) tags.push('rebel');
  if (titleLower.includes('imperial') || titleLower.includes('empire')) tags.push('empire');
  if (titleLower.includes('republic')) tags.push('republic');
  if (titleLower.includes('separatist')) tags.push('separatist');

  return { category, tags };
}

// Extract article content from HTML
function extractArticleContent(html: string, url: string): Article | null {
  const $ = cheerio.load(html);

  // Get title
  const title = $('h3.post-title').first().text().trim() ||
                $('h1.post-title').first().text().trim() ||
                $('title').text().replace(' - Cannot Get Your Ship Out', '').trim();

  if (!title) {
    console.log('  Warning: No title found');
    return null;
  }

  // Get date
  const dateText = $('abbr.published').attr('title') ||
                   $('.date-header span').first().text().trim() ||
                   '';

  // Get main content
  const contentElement = $('.post-body').first();

  // Remove scripts, styles, and ads
  contentElement.find('script, style, .post-share-buttons, .post-footer').remove();

  // Get text content, preserving some structure
  let content = '';
  contentElement.find('p, h1, h2, h3, h4, li').each((_, el) => {
    const text = $(el).text().trim();
    if (text) {
      const tagName = $(el).prop('tagName')?.toLowerCase();
      if (tagName?.startsWith('h')) {
        content += `\n## ${text}\n`;
      } else if (tagName === 'li') {
        content += `- ${text}\n`;
      } else {
        content += `${text}\n\n`;
      }
    }
  });

  content = content.trim();

  if (!content || content.length < 100) {
    // Fallback to full text
    content = contentElement.text().trim();
  }

  if (!content || content.length < 50) {
    console.log('  Warning: No content found');
    return null;
  }

  const { category, tags } = categorizeArticle(title, content);

  return {
    title,
    url,
    date: dateText,
    content,
    category,
    tags,
  };
}

// Get all article URLs from the blog archive
async function getArticleUrls(): Promise<string[]> {
  const urls: string[] = [];

  // Blogger sites have an archive widget, but we can also use the sitemap
  // Let's try fetching the main page and following archive links

  // First, try the sitemap
  try {
    const sitemapUrl = `${BLOG_URL}/sitemap.xml`;
    const sitemapHtml = await fetchPage(sitemapUrl);
    const $ = cheerio.load(sitemapHtml, { xmlMode: true });

    $('url loc').each((_, el) => {
      const url = $(el).text();
      if (url && url.includes('/20') && !url.includes('/search/')) {
        urls.push(url);
      }
    });

    if (urls.length > 0) {
      console.log(`Found ${urls.length} articles from sitemap`);
      return urls;
    }
  } catch (e) {
    console.log('Sitemap not available, trying archive method...');
  }

  // Fallback: scrape the archive page
  const mainPageHtml = await fetchPage(BLOG_URL);
  const $ = cheerio.load(mainPageHtml);

  // Look for archive links
  const archiveLinks: string[] = [];
  $('a[href*="/search/label/"], a[href*="archive"]').each((_, el) => {
    const href = $(el).attr('href');
    if (href) archiveLinks.push(href);
  });

  // Also get recent posts from main page
  $('a[href*=".blogspot.com/20"]').each((_, el) => {
    const href = $(el).attr('href');
    if (href && href.includes('/20') && !href.includes('/search/') && !urls.includes(href)) {
      urls.push(href);
    }
  });

  // Try to find more through pagination or archive
  // Blogger typically has posts at /YYYY/MM/title.html format
  // Let's try fetching multiple archive pages

  for (let year = 2016; year <= 2025; year++) {
    for (let month = 1; month <= 12; month++) {
      try {
        const archiveUrl = `${BLOG_URL}/${year}/${month.toString().padStart(2, '0')}`;
        await delay(500); // Rate limit
        const archiveHtml = await fetchPage(archiveUrl);
        const $archive = cheerio.load(archiveHtml);

        $archive('a[href*=".blogspot.com/20"]').each((_, el) => {
          const href = $archive(el).attr('href');
          if (href && href.includes(`/${year}/`) && !href.includes('/search/') && !urls.includes(href)) {
            urls.push(href);
          }
        });
      } catch {
        // Month doesn't exist or no posts, continue
      }
    }
  }

  console.log(`Found ${urls.length} articles from archive scraping`);
  return [...new Set(urls)]; // Remove duplicates
}

// Make filename safe
function safeFilename(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);
}

async function main() {
  console.log('========================================');
  console.log('  CGYSO Article Downloader');
  console.log('========================================\n');

  // Create output directory
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // Create category subdirectories
  const categories = ['commanders', 'ships', 'squadrons', 'upgrades', 'tactics', 'fleet-building', 'general'];
  for (const cat of categories) {
    const catDir = path.join(OUTPUT_DIR, cat);
    if (!fs.existsSync(catDir)) {
      fs.mkdirSync(catDir, { recursive: true });
    }
  }

  console.log('Step 1: Finding all article URLs...\n');
  const articleUrls = await getArticleUrls();

  if (articleUrls.length === 0) {
    console.log('No articles found!');
    return;
  }

  console.log(`\nStep 2: Downloading ${articleUrls.length} articles...\n`);

  const articles: Article[] = [];
  const index: ArticleIndex = {
    downloadedAt: new Date().toISOString(),
    totalArticles: 0,
    categories: {},
    articles: [],
  };

  for (let i = 0; i < articleUrls.length; i++) {
    const url = articleUrls[i];
    console.log(`[${i + 1}/${articleUrls.length}] Processing: ${url.slice(0, 80)}...`);

    try {
      await delay(1000); // Rate limit - 1 second between requests
      const html = await fetchPage(url);
      const article = extractArticleContent(html, url);

      if (article) {
        articles.push(article);

        // Save article to file
        const filename = `${safeFilename(article.title)}.md`;
        const filepath = path.join(OUTPUT_DIR, article.category, filename);

        const markdown = `# ${article.title}

**Source:** ${article.url}
**Date:** ${article.date}
**Category:** ${article.category}
**Tags:** ${article.tags.join(', ')}

---

${article.content}
`;

        fs.writeFileSync(filepath, markdown);

        // Update index
        index.categories[article.category] = (index.categories[article.category] || 0) + 1;
        index.articles.push({
          title: article.title,
          url: article.url,
          date: article.date,
          category: article.category,
          filename: `${article.category}/${filename}`,
        });

        console.log(`  ✓ Saved: ${article.category}/${filename}`);
      }
    } catch (error) {
      console.log(`  ✗ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Save index
  index.totalArticles = articles.length;
  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'index.json'),
    JSON.stringify(index, null, 2)
  );

  console.log('\n========================================');
  console.log('  Download Complete!');
  console.log('========================================');
  console.log(`Total articles: ${articles.length}`);
  console.log('\nBy category:');
  for (const [cat, count] of Object.entries(index.categories)) {
    console.log(`  ${cat}: ${count}`);
  }
  console.log(`\nArticles saved to: ${OUTPUT_DIR}`);
}

main().catch(console.error);
