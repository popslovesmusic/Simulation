# Archive - Obsolete Web Interface Files

**Archive Date:** November 10, 2025
**Reason:** Superseded by modular ES6 architecture

---

## Archived Files

### 1. `dase_interface_2025-11-10.html` (2053 lines)

**Original Name:** `dase_interface.html`

**Description:**
Fully functional monolithic web interface for DASE Analog Excel. Contains all HTML, CSS, and JavaScript in a single file.

**Why Archived:**
- Monolithic architecture (HTML + CSS + JS in one file)
- Hard to maintain and test
- Global scope pollution
- Cannot be modularized or bundled
- Superseded by modular version in parent directory

**What It Contained:**
- Complete grid implementation (50×26 cells)
- Symbol palette with 19 components across 5 categories
- 100+ formula presets
- Drag-and-drop functionality
- Terminal integration (mock DASE CLI)
- Simulation controls
- Properties panel
- All DVSL and IGS-OA symbols

**Status:** FUNCTIONAL but OBSOLETE
**Last Working Date:** November 10, 2025

**Code to Extract:**
All business logic from this file needs to be extracted into ES6 modules. See `../WEB_INTERFACE_ANALYSIS.md` for extraction plan.

---

### 2. `complete_dvsl_interface_2025-11-10.html`

**Original Name:** `complete_dvsl_interface.html`

**Description:**
Older version of monolithic interface. Appears to be a previous iteration of `dase_interface.html`.

**Why Archived:**
- Older version
- Likely duplicate functionality
- Superseded by newer implementations

**Status:** OBSOLETE
**Last Modified:** Unknown (predates current session)

---

## Migration Path

The functionality from these archived files is being migrated to the modular architecture:

### From Monolithic → Modular

| Feature | Old Location | New Location | Status |
|---------|-------------|--------------|--------|
| Grid system | Inline `<script>` | `js/components/Grid.js` | ❌ Pending |
| Symbol library | Inline `<script>` | `js/components/ComponentLibrary.js` | ❌ Pending |
| Cell data model | Inline `<script>` | `js/core/CellData.js` | ❌ Pending |
| Formula parser | Inline `<script>` | `js/utils/FormulaParser.js` | ❌ Pending |
| Properties panel | Inline `<script>` | `js/components/PropertiesPanel.js` | ❌ Pending |
| Simulation engine | Inline `<script>` | `js/core/SimulationEngine.js` | ❌ Pending |
| Symbol definitions | Inline object | `js/data/symbols.js` | ❌ Pending |
| Formula presets | Inline object | `js/data/presets.js` | ❌ Pending |
| Styling | Inline `<style>` | `css/*.css` | ✅ **COMPLETE** |
| Terminal | Inline `<script>` | `js/components/Terminal.js` | ✅ **COMPLETE** |
| Network layer | Mock functions | `js/network/EngineClient.js` | ✅ **COMPLETE** |

---

## Why the Change?

### Problems with Monolithic Architecture

1. **Maintainability:** 2000+ lines in one file is difficult to navigate
2. **Testing:** Cannot unit test individual components
3. **Collaboration:** Multiple developers cannot work simultaneously
4. **Reusability:** Cannot reuse components in other projects
5. **Build Process:** Cannot minify, tree-shake, or bundle efficiently
6. **Version Control:** Single file means merge conflicts
7. **Code Organization:** No clear separation of concerns
8. **Performance:** Must load entire file even if only using part of it

### Benefits of Modular Architecture

1. ✅ **Separation of Concerns:** HTML, CSS, JS in separate files
2. ✅ **ES6 Modules:** Import/export with proper scoping
3. ✅ **Testability:** Can unit test each module independently
4. ✅ **Maintainability:** Each file has single responsibility
5. ✅ **Reusability:** Components can be imported anywhere
6. ✅ **Build System:** Compatible with webpack, rollup, vite
7. ✅ **Performance:** Can lazy-load modules as needed
8. ✅ **Developer Experience:** Better IDE support, autocomplete
9. ✅ **Scalability:** Easy to add new features
10. ✅ **Team Collaboration:** Multiple developers can work in parallel

---

## Restoration Instructions

If you need to restore the archived functionality:

### Option 1: Use Archived File (Quick Test)

```bash
# Copy archived file back to web root
cp archive/dase_interface_2025-11-10.html index_restored.html

# Open in browser
# File path: file:///D:/igsoa-sim/web/index_restored.html
```

**Note:** This will give you a working interface but with all the problems of monolithic architecture.

### Option 2: Complete the Modular Migration (Recommended)

Follow the extraction plan in `../WEB_INTERFACE_ANALYSIS.md`:

1. Extract Grid.js from archived file
2. Extract ComponentLibrary.js
3. Extract other modules as documented
4. Test integration with existing modules
5. Achieve feature parity with archived version

**Estimated Time:** 12-14 hours

---

## File Integrity

### SHA256 Checksums (if needed for verification)

To generate checksums:
```bash
cd D:/igsoa-sim/web/archive
sha256sum dase_interface_2025-11-10.html > checksums.txt
sha256sum complete_dvsl_interface_2025-11-10.html >> checksums.txt
```

---

## Archive Policy

**Retention Period:** Indefinite (until modular version reaches 100% feature parity)

**Review Date:** December 10, 2025 (30 days)

**Deletion Criteria:**
- [ ] Modular version has 100% feature parity
- [ ] All functionality tested and working
- [ ] No regression bugs in modular version
- [ ] Team consensus on deletion

**Until then:** KEEP archived files as reference and fallback

---

## Contact

For questions about the migration or to request restoration:
- See: `../WEB_INTERFACE_ANALYSIS.md`
- Refer to: IGSOA project documentation

---

**Archive Maintained By:** IGSOA Development Team
**Archive Location:** `D:\igsoa-sim\web\archive\`
**Last Updated:** November 10, 2025
