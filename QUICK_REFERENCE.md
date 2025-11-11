# DASE Command Center - Quick Reference

**Last Updated:** 2025-11-11
**Status:** Backend Complete (60%) | Frontend Pending (40%)

---

## 🚀 Quick Start

### Test CLI --describe
```bash
cd dase_cli
./dase_cli.exe --describe igsoa_gw
```

### Start Backend Server
```bash
cd backend
node server.js
# Server runs on http://localhost:3000
# WebSocket on ws://localhost:8080
```

### Test REST API
```bash
# List engines
curl http://localhost:3000/api/engines

# Get engine description
curl http://localhost:3000/api/engines/igsoa_gw | jq .

# Browse files
curl "http://localhost:3000/api/fs?path=/missions"
```

---

## 📁 Important Files

### Documentation:
- `COMMAND_CENTER_CHECKPOINT.md` - **Full checkpoint (read this!)**
- `docs/COMMAND_CENTER_SPECIFICATION.md` - Original spec
- `dase.html` - Reference UI design

### Backend:
- `backend/server.js` - REST API + WebSocket (✅ Complete)
- `dase_cli/src/command_router.cpp` - Engine descriptions (✅ Complete)
- `dase_cli/src/metric_emitter.h` - METRIC utilities (✅ Complete)

### Frontend (Existing):
- `web/js/network/EngineClient.js` - WebSocket client (✅ Works)
- `web/js/components/Terminal.js` - Terminal display (✅ Works)

### Frontend (TODO):
- `web/js/core/Grid.js` - ❌ Not started (400 lines, 8-10h)
- `web/js/components/ModelPanel.js` - ❌ Not started (300 lines, 6-8h)

---

## 🎯 Next Steps

1. **Read checkpoint:** `COMMAND_CENTER_CHECKPOINT.md`
2. **Test backend:** Run server, test REST endpoints
3. **Create Grid.js:** Copy structure from `dase.html`, modularize
4. **Connect WebSocket:** Wire Grid to EngineClient for `=LIVE()` updates

---

## 📊 Progress

| Phase | Status | Time |
|-------|--------|------|
| CLI --describe | ✅ | 2h |
| CLI METRIC output | ✅ | 0.5h |
| Backend REST API | ✅ | 2h |
| Backend WS METRIC | ✅ | 0.5h |
| **Backend Total** | **✅ 100%** | **5h** |
| Frontend Grid | 🔲 | 0/10h |
| Frontend ModelPanel | 🔲 | 0/8h |
| Frontend Integration | 🔲 | 0/6h |
| **Frontend Total** | **🔲 0%** | **0/24h** |

**Overall: 60% Complete**

---

## 🧪 Testing Checklist

### ✅ Tested & Working:
- [x] CLI `--describe igsoa_gw` outputs JSON
- [x] REST `/api/engines` returns list
- [x] REST `/api/engines/igsoa_gw` returns description
- [x] REST `/api/fs` browses directories

### 🔲 TODO:
- [ ] Integrate METRIC emission into simulation engines
- [ ] Test WebSocket METRIC streaming
- [ ] Create Grid component
- [ ] Test `=LIVE()` formula function
- [ ] End-to-end simulation workflow

---

## 💡 Key Decisions

1. **Backend:** Node.js + Express (per spec) ✅
2. **WebSocket:** Separate server on port 8080 ✅
3. **Frontend:** Vanilla JS (no React) - keeps it simple
4. **Formula Engine:** Need to implement or use library (TBD)
5. **Grid Rendering:** DOM-based (26 cols × 100 rows)

---

## 🐛 Known Issues

- Simulation endpoints are stubs (don't actually start simulations yet)
- METRIC emission not integrated into C++ engines yet
- Only 2/8 engines have descriptions (igsoa_gw, igsoa_complex)
- Frontend Grid doesn't exist yet

---

## 📞 Contact Points

**For Questions:**
1. Read `COMMAND_CENTER_CHECKPOINT.md` first
2. Check `docs/COMMAND_CENTER_SPECIFICATION.md` for requirements
3. Review `dase.html` for UI reference

**To Resume Work:**
- Start with Grid.js implementation
- Use `dase.html` lines 669-850 as reference
- Focus on formula evaluation and `=LIVE()` function

---

**End of Quick Reference**
