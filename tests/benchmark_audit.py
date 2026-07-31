import os
import tempfile
import time
import sys
from pychronicle.storage import StateStorage
from pychronicle.tracer import Tracer

def main():
    print("=" * 60)
    print("          PYCHRONICLE BENCHMARK & STORAGE AUDIT          ")
    print("=" * 60)

    # 1. Generate the complex loop code script where variables are guaranteed
    # to change on every iteration to accurately count execution steps.
    code = """
def run_benchmark():
    total_sum = 0
    items = []
    # 50 outer loop runs * 25 inner loop runs = 1250 total iterations
    # Each iteration: i, j, val, total_sum, and items mutate
    for i in range(50):
        for j in range(25):
            val = (i + 1) * (j + 1)
            total_sum += val
            items.append(val)
    return total_sum

result = run_benchmark()
"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        temp_path = f.name

    try:
        # 2. Initialize in-memory storage
        storage = StateStorage(":memory:")
        tracer = Tracer(temp_path, storage)

        print("[*] Running tracer on complex nested loop...")
        start_time = time.perf_counter()
        tracer.run()
        end_time = time.perf_counter()
        
        elapsed_seconds = end_time - start_time
        print(f"[+] Execution trace completed in {elapsed_seconds:.4f} seconds.")

        # 3. Retrieve and audit database records
        history = storage.get_history()
        total_mutations = len(history)
        print(f"[+] Total variable mutations logged: {total_mutations}")

        # Compute averages
        if total_mutations > 0:
            avg_write_latency_ms = (elapsed_seconds * 1000) / total_mutations
            print(f"[+] Average state write latency: {avg_write_latency_ms:.4f} ms per record.")
        else:
            avg_write_latency_ms = 0
            print("[-] Warning: No mutations logged!")

        # 4. Perform Trace Validation (Verify no dropped frames/mutations)
        print("\n[*] Auditing variable mutation counts...")
        mutations_by_var = {}
        for h in history:
            var = h["variable_name"]
            mutations_by_var[var] = mutations_by_var.get(var, 0) + 1

        print(f"    - 'i' mutations: {mutations_by_var.get('i', 0)} (Expected: 50)")
        print(f"    - 'j' mutations: {mutations_by_var.get('j', 0)} (Expected: 1250)")
        print(f"    - 'val' mutations: {mutations_by_var.get('val', 0)} (Expected: 1250)")
        print(f"    - 'total_sum' mutations: {mutations_by_var.get('total_sum', 0)} (Expected: 1251)")
        print(f"    - 'items' mutations: {mutations_by_var.get('items', 0)} (Expected: 1251)")

        # Verify counts
        assert mutations_by_var.get("i", 0) == 50, f"Expected 50 'i' mutations, got {mutations_by_var.get('i', 0)}"
        assert mutations_by_var.get("j", 0) == 1250, f"Expected 1250 'j' mutations, got {mutations_by_var.get('j', 0)}"
        assert mutations_by_var.get("val", 0) == 1250, f"Expected 1250 'val' mutations, got {mutations_by_var.get('val', 0)}"
        assert mutations_by_var.get("total_sum", 0) == 1251, f"Expected 1251 'total_sum' mutations, got {mutations_by_var.get('total_sum', 0)}"
        assert mutations_by_var.get("items", 0) == 1251, f"Expected 1251 'items' mutations, got {mutations_by_var.get('items', 0)}"
        
        print("\n[OK] TRACE VALIDATION: Success! 100% of frame mutations captured correctly (0 dropped).")
        
        # 5. Storage Audit Verification
        # Check that average insertion latency is fast
        assert avg_write_latency_ms < 0.5, f"Warning: Storage write latency too high: {avg_write_latency_ms:.4f} ms"
        print("[OK] STORAGE AUDIT: Success! DB write throughput meets sub-0.5ms target latency constraint.")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] BENCHMARK FAILED: {str(e)}")
        sys.exit(1)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    main()
