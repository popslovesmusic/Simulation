/**
 * Frontend Bundle Analysis Script
 *
 * Analyzes Vite build output to identify:
 * - Bundle size
 * - Largest dependencies
 * - Code splitting effectiveness
 * - Optimization opportunities
 *
 * Usage:
 *   cd web/command-center
 *   npm run build
 *   node ../../scripts/analyze_bundle.js
 */

const fs = require('fs');
const path = require('path');

class BundleAnalyzer {
  constructor(distPath = './web/command-center/dist') {
    this.distPath = distPath;
    this.results = {
      timestamp: new Date().toISOString(),
      totalSize: 0,
      files: [],
      recommendations: [],
    };
  }

  analyzeDirectory(dir) {
    const files = fs.readdirSync(dir);

    for (const file of files) {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);

      if (stat.isDirectory()) {
        this.analyzeDirectory(filePath);
      } else {
        const ext = path.extname(file);
        const size = stat.size;

        this.results.files.push({
          path: path.relative(this.distPath, filePath),
          size: size,
          sizeKB: (size / 1024).toFixed(2),
          sizeMB: (size / (1024 * 1024)).toFixed(2),
          type: ext,
        });

        this.results.totalSize += size;
      }
    }
  }

  generateReport() {
    console.log('='.repeat(60));
    console.log('FRONTEND BUNDLE ANALYSIS');
    console.log('='.repeat(60));
    console.log(`Timestamp: ${this.results.timestamp}`);
    console.log(`Build directory: ${this.distPath}`);
    console.log();

    // Total size
    const totalMB = (this.results.totalSize / (1024 * 1024)).toFixed(2);
    console.log(`Total bundle size: ${totalMB} MB`);
    console.log();

    // Sort files by size
    const sortedFiles = [...this.results.files].sort((a, b) => b.size - a.size);

    // Largest files
    console.log('Top 10 Largest Files:');
    console.log('-'.repeat(60));
    sortedFiles.slice(0, 10).forEach((file, i) => {
      console.log(`${i + 1}. ${file.path}`);
      console.log(`   Size: ${file.sizeKB} KB`);
    });
    console.log();

    // Files by type
    const byType = {};
    this.results.files.forEach(file => {
      if (!byType[file.type]) {
        byType[file.type] = { count: 0, size: 0 };
      }
      byType[file.type].count++;
      byType[file.type].size += file.size;
    });

    console.log('Files by Type:');
    console.log('-'.repeat(60));
    Object.entries(byType)
      .sort((a, b) => b[1].size - a[1].size)
      .forEach(([type, data]) => {
        const sizeMB = (data.size / (1024 * 1024)).toFixed(2);
        console.log(`${type || '(no extension)'}: ${data.count} files, ${sizeMB} MB`);
      });
    console.log();

    // Analysis
    this.analyzePerformance();

    // Recommendations
    if (this.results.recommendations.length > 0) {
      console.log('Recommendations:');
      console.log('-'.repeat(60));
      this.results.recommendations.forEach((rec, i) => {
        console.log(`${i + 1}. ${rec}`);
      });
      console.log();
    }

    console.log('='.repeat(60));
    console.log('ANALYSIS COMPLETE');
    console.log('='.repeat(60));
  }

  analyzePerformance() {
    const jsFiles = this.results.files.filter(f => f.type === '.js');
    const cssFiles = this.results.files.filter(f => f.type === '.css');

    const totalJS = jsFiles.reduce((sum, f) => sum + f.size, 0);
    const totalCSS = cssFiles.reduce((sum, f) => sum + f.size, 0);

    const totalJSMB = (totalJS / (1024 * 1024)).toFixed(2);
    const totalCSSMB = (totalCSS / (1024 * 1024)).toFixed(2);

    console.log('Performance Analysis:');
    console.log('-'.repeat(60));
    console.log(`JavaScript: ${totalJSMB} MB (${jsFiles.length} files)`);
    console.log(`CSS: ${totalCSSMB} MB (${cssFiles.length} files)`);
    console.log();

    // Check for large files (> 500 KB)
    const largeFiles = this.results.files.filter(f => f.size > 500 * 1024);
    if (largeFiles.length > 0) {
      console.log(`⚠️  Found ${largeFiles.length} files > 500 KB`);
      this.results.recommendations.push(
        'Consider code splitting for large bundles (>500 KB)'
      );
    }

    // Check for unminified files
    const potentiallyUnminified = this.results.files.filter(
      f => f.path.includes('.js') && !f.path.includes('.min.') && f.size > 100 * 1024
    );
    if (potentiallyUnminified.length > 0) {
      this.results.recommendations.push(
        'Ensure all JavaScript is minified in production build'
      );
    }

    // Check total size
    const totalMB = this.results.totalSize / (1024 * 1024);
    if (totalMB > 5) {
      this.results.recommendations.push(
        `Total bundle size (${totalMB.toFixed(2)} MB) is large. Target: < 2 MB`
      );
    } else if (totalMB > 2) {
      this.results.recommendations.push(
        `Total bundle size (${totalMB.toFixed(2)} MB) is moderate. Consider optimization`
      );
    } else {
      console.log(`✓ Total bundle size (${totalMB.toFixed(2)} MB) is good`);
    }

    console.log();
  }

  saveReport() {
    const reportPath = path.join('reports', 'profiling', `bundle_analysis_${Date.now()}.json`);

    // Ensure directory exists
    const dir = path.dirname(reportPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(reportPath, JSON.stringify(this.results, null, 2));
    console.log(`\nReport saved to: ${reportPath}`);
  }

  run() {
    if (!fs.existsSync(this.distPath)) {
      console.error(`Error: Build directory not found: ${this.distPath}`);
      console.error('Please run "npm run build" first in web/command-center/');
      process.exit(1);
    }

    this.analyzeDirectory(this.distPath);
    this.generateReport();
    this.saveReport();
  }
}

// Run analysis
const analyzer = new BundleAnalyzer();
analyzer.run();
