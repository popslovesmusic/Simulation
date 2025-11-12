const express = require('express');
const fs = require('fs');
const path = require('path');

const DOCS_ROOT = path.join(__dirname, '..', '..', '..', 'docs', 'command-center');
const TUTORIALS_DIR = path.join(DOCS_ROOT, 'tutorials');
const GLOSSARY_DIR = path.join(DOCS_ROOT, 'glossary');

function ensureDirectories() {
  for (const dir of [TUTORIALS_DIR, GLOSSARY_DIR]) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }
}

function readDocumentIndex(directory) {
  ensureDirectories();
  const entries = fs.readdirSync(directory, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.md'))
    .map((entry) => {
      const fullPath = path.join(directory, entry.name);
      const content = fs.readFileSync(fullPath, 'utf-8');
      const [firstLine] = content.split('\n');
      const title = firstLine.replace(/^#+\s*/, '').trim() || entry.name.replace(/\.md$/, '');
      return {
        slug: entry.name.replace(/\.md$/, ''),
        title,
        summary: content.split('\n').slice(1, 4).join(' ').slice(0, 280),
      };
    });
}

function readDocument(directory, slug) {
  ensureDirectories();

  // Fix: 2025-03 Code Review - Prevent path traversal with proper normalization
  const resolvedDir = path.resolve(directory);
  const resolvedPath = path.resolve(directory, `${slug}.md`);

  // Security: Ensure resolved path is still inside the directory
  if (!resolvedPath.startsWith(resolvedDir + path.sep)) {
    throw new Error('Invalid slug: path traversal attempt blocked');
  }

  if (!fs.existsSync(resolvedPath)) {
    return null;
  }
  const content = fs.readFileSync(resolvedPath, 'utf-8');
  const [firstLine, ...rest] = content.split('\n');
  const title = firstLine.replace(/^#+\s*/, '').trim() || slug;
  return { title, content: rest.join('\n').trim() };
}

const router = express.Router();

router.get('/tutorials', (_req, res) => {
  try {
    const tutorials = readDocumentIndex(TUTORIALS_DIR);
    res.json({ tutorials });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/tutorials/:slug', (req, res) => {
  try {
    const doc = readDocument(TUTORIALS_DIR, req.params.slug);
    if (!doc) {
      res.status(404).json({ error: 'Tutorial not found' });
      return;
    }
    res.json(doc);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

router.get('/glossary', (_req, res) => {
  try {
    const glossary = readDocumentIndex(GLOSSARY_DIR).map((entry) => ({
      ...entry,
      type: 'definition',
    }));
    res.json({ glossary });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/glossary/:slug', (req, res) => {
  try {
    const doc = readDocument(GLOSSARY_DIR, req.params.slug);
    if (!doc) {
      res.status(404).json({ error: 'Glossary entry not found' });
      return;
    }
    res.json(doc);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

module.exports = { tutorialsRouter: router };
