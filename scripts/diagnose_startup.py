#!/usr/bin/env python3
"""Diagnose FastAPI startup performance to identify bottlenecks.

This script instruments the dependency loading process to measure
timing of each component initialization.
"""
import sys
import time
from pathlib import Path

# Add services to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "services" / "analysis-service"))
sys.path.insert(0, str(repo_root / "services" / "common"))

def time_operation(name: str):
    """Context manager to time an operation."""
    class TimerContext:
        def __enter__(self):
            self.start = time.perf_counter()
            print(f"⏱️  Starting: {name}")
            return self

        def __exit__(self, *args):
            elapsed = time.perf_counter() - self.start
            print(f"✅ Completed: {name} ({elapsed:.3f}s)")
            return False

    return TimerContext()


def main():
    """Instrument the startup process."""
    print("\n" + "="*70)
    print("🔍 FastAPI Startup Performance Diagnosis")
    print("="*70 + "\n")

    total_start = time.perf_counter()

    # Step 1: Import FastAPI
    with time_operation("Import FastAPI"):
        from fastapi import FastAPI

    # Step 2: Import app factory
    with time_operation("Import services.common"):
        from services.common import create_service_app

    # Step 3: Create FastAPI app
    with time_operation("Create FastAPI app"):
        app = create_service_app(
            app_name="saju-analysis-service",
            version="0.1.0",
            rule_id="KR_classic_v1.4"
        )

    # Step 4: Import app dependencies
    with time_operation("Import app.api.dependencies"):
        from app.api.dependencies import preload_dependencies

    # Step 5: Instrument individual singletons
    print("\n" + "-"*70)
    print("Loading Singletons:")
    print("-"*70 + "\n")

    with time_operation("Load AnalysisEngine singleton"):
        from app.api.dependencies import _analysis_engine_singleton
        engine = _analysis_engine_singleton()

    with time_operation("Load LLMGuard singleton"):
        from app.api.dependencies import _llm_guard_singleton
        guard = _llm_guard_singleton()

    # Step 6: Create TestClient
    print("\n" + "-"*70)
    print("Testing with TestClient:")
    print("-"*70 + "\n")

    with time_operation("Create TestClient"):
        from fastapi.testclient import TestClient
        client = TestClient(app, raise_server_exceptions=True)

    with time_operation("First /health request"):
        response = client.get("/health")
        assert response.status_code == 200
        print(f"   Response: {response.json()}")

    with time_operation("Second /health request (cached)"):
        response = client.get("/health")
        assert response.status_code == 200

    total_elapsed = time.perf_counter() - total_start

    print("\n" + "="*70)
    print(f"✅ Total startup time: {total_elapsed:.3f}s")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
