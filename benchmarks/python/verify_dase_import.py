import importlib
import inspect
import sys

print("🔍 Importing dase_engine...")
try:
    de = importlib.import_module("dase_engine")
    print("✅ Module imported successfully!\n")
except Exception as e:
    print("❌ Import failed:", e)
    sys.exit(1)

print("📦 Module attributes:")
for name in dir(de):
    if not name.startswith("_"):
        print("  ", name)

print("\n🧠 Checking key classes...")
expected = ["CPUFeatures", "EngineMetrics", "AnalogUniversalNodeAVX2", "AnalogCellularEngineAVX2"]
for cls in expected:
    print(f"{cls:28}", "✅" if hasattr(de, cls) else "❌ missing")

print("\n⚙️ Testing CPU feature access:")
try:
    print("AVX2:", de.CPUFeatures.has_avx2())
    print("FMA :", de.CPUFeatures.has_fma())
    de.CPUFeatures.print_capabilities()
except Exception as e:
    print("CPUFeatures test failed:", e)

print("\n🧩 Testing EngineMetrics:")
try:
    m = de.EngineMetrics()
    m.reset()
    print("EngineMetrics OK")
except Exception as e:
    print("EngineMetrics failed:", e)
