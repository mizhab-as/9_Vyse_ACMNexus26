# Real Data Setup - 1 Minute

## Just 1 File Change

### BEFORE (Synthetic Data)
```bash
# Terminal 3:
python streaming_simulator.py
```

### AFTER (Real MIMIC Data) ✅
```bash
# Terminal 3:
python streaming_real_data.py
```

**That's it. Everything else is identical.**

---

## What's Different?

- ❌ Fake synthetic vitals
- ✅ **Real MIMIC-III patient records**
- ❌ "Obviously generated"
- ✅ **Authentic septic shock progression**

---

## Full System (3 Terminals)

```bash
# Terminal 1
cd backend && python -m uvicorn main:app --reload

# Terminal 2
cd frontend && npm start

# Terminal 3 ← NEW FILE
python streaming_real_data.py
```

Visit: **http://localhost:3000**

---

## What Judges See

```
[REAL DATA] Loading p000009_sepsis.psv...
[REAL DATA] Total samples: 258 (~43.0 minutes)

✓  STABLE | Sample   0 | HR:  80 | BP: 120/80 | O2: 95%
✓  STABLE | Sample  50 | HR:  85 | BP: 118/79 | O2: 97%
⚠️  WARN  | Sample 100 | HR: 105 | BP: 110/70 | O2: 94%
🚨 CRISIS | Sample 145 | HR: 125 | BP:  88/45 | O2: 89%

[DONE] Crisis detected at: Sample 145 (24.2 minutes)
```

✅ Real progression
✅ Actual patient data
✅ Authentic anomalies

---

## Files Available

You have 2 real datasets already:

```
data_simulator/p000001_stable.psv      (8.9 KB)  - Normal vitals
data_simulator/p000009_sepsis.psv      (41 KB)   - Crisis progression ← DEFAULT
```

**Note:** Default uses `p000009_sepsis.psv` (best for demos)

To use different file, edit line in `streaming_real_data.py`:
```python
psv_file = "data_simulator/p000001_stable.psv"  # ← Change here
```

---

## More Real Data?

Get additional MIMIC-III datasets:
1. Register at https://mimic.physionet.org/
2. Download .psv files
3. Save to `data_simulator/`
4. Works automatically!

---

## That's All!

You now have:
- 🎉 Real patient data (not synthetic)
- 🎉 Authentic crisis patterns
- 🎉 Judges impressed
- 🎉 Same dashboard experience

Go code! 🚀

