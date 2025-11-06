# Development Shell Guide

**Version:** 1.0.0
**Date:** 2025-11-06
**Tool:** `scripts/devshell.py`

## Overview

The **devshell** is an interactive Python environment pre-configured with all saju-engine services, utilities, and sample data. It provides an IPython-based REPL for rapid prototyping, testing, and exploration.

**Use Cases:**
- 🧪 Testing engine behavior interactively
- 🔍 Exploring analysis results
- 🐛 Debugging complex issues
- 📊 Prototyping new features
- 📚 Learning the codebase

---

## Quick Start

**Prerequisites:**
- Virtual environment activated (`.venv/bin/python`)
- `sitecustomize.py` present at repo root (required until Task 5 - Pydantic Settings)
- IPython installed (`pip install ipython` - already included in dev dependencies)

### Basic Usage

```bash
# Start interactive shell
.venv/bin/python scripts/devshell.py

# Start with specific service
python scripts/devshell.py --service analysis

# Run a script with devshell context
python scripts/devshell.py --script my_test.py

# Suppress banner
python scripts/devshell.py --no-banner
```

### First Commands

```python
# Show help
help_devshell()

# Analyze sample data
result = analysis_engine.analyze(sample_request)
print(result.strength.level)  # Output: '신강'

# Inspect object
result?                        # Show info
result??                       # Show source code

# List variables
%whos
```

---

## Features

### 1. Pre-loaded Services

**Analysis Service:**
- `analysis_engine` - Ready-to-use AnalysisEngine instance
- `AnalysisEngine` - Class for creating new instances
- `AnalysisRequest` - Request model
- `PillarInput` - Pillar input model

**Common Utilities:**
- `Container` - DI container class
- `container` - Default container instance
- `create_service_app` - FastAPI app factory
- `resolve_policy_path` - Policy file resolver
- `ValidationError`, `NotFoundError` - Exceptions

### 2. Sample Data

**Built-in Test Data:**
```python
# Pre-built four pillars
sample_pillars = {
    "year": {"pillar": "庚辰"},
    "month": {"pillar": "乙酉"},
    "day": {"pillar": "乙亥"},
    "hour": {"pillar": "辛巳"},
}

# Pre-built analysis request
sample_request  # AnalysisRequest instance
```

### 3. IPython Enhancements

- **Syntax highlighting** - Color-coded output
- **Tab completion** - Auto-complete for objects
- **Command history** - Up/down arrows to recall
- **Magic commands** - %whos, %debug, %timeit, etc.
- **Custom prompt** - `사주 [1]:` style

---

## Common Workflows

### Workflow 1: Test Analysis

```python
# Start shell
$ python scripts/devshell.py

# Use pre-built sample
사주 [1]: result = analysis_engine.analyze(sample_request)

# Inspect results
사주 [2]: result.strength.level
Out[2]: '신강'

사주 [3]: result.ten_gods.summary
Out[3]: {'비견': 2, '식신': 1, '정재': 1, ...}

사주 [4]: result.relations.chong
Out[4]: [{'pair': ['巳', '亥'], 'severity': 'high'}]
```

### Workflow 2: Create Custom Request

```python
# Create pillars
pillars = {
    "year": PillarInput(pillar="甲子"),
    "month": PillarInput(pillar="丙寅"),
    "day": PillarInput(pillar="戊辰"),
    "hour": PillarInput(pillar="庚午"),
}

# Create request
request = AnalysisRequest(
    pillars=pillars,
    options={
        "birth_dt": "1984-02-04T15:30:00+09:00",
        "timezone": "Asia/Seoul"
    }
)

# Analyze
result = analysis_engine.analyze(request)
print(f"Strength: {result.strength.level}")
print(f"Score: {result.strength_details.total}")
```

### Workflow 3: Test Container

```python
# Check current engine
engine1 = container.get("get_analysis_engine")
engine2 = container.get("get_analysis_engine")
assert engine1 is engine2  # Same instance (singleton)

# Override for testing
from unittest.mock import Mock
mock_engine = Mock()
mock_engine.analyze.return_value = {"mocked": True}

with container.override("get_analysis_engine", mock_engine):
    engine = container.get("get_analysis_engine")
    assert engine is mock_engine
    result = engine.analyze(sample_request)
    print(result)  # {'mocked': True}
```

### Workflow 4: Explore Policies

```python
# Find policy file
policy_path = resolve_policy_path("strength_policy_v2.json")
print(policy_path)

# Load and inspect
import json
with open(policy_path) as f:
    policy = json.load(f)

# Check buckets
for bucket in policy["buckets"]:
    print(f"{bucket['code']}: {bucket['min']}-{bucket['max']}")
```

### Workflow 5: Profile Performance

```python
# Time analysis
%timeit analysis_engine.analyze(sample_request)

# Profile detailed
%prun analysis_engine.analyze(sample_request)

# Memory usage
import sys
result = analysis_engine.analyze(sample_request)
sys.getsizeof(result)
```

### Workflow 6: Debug Errors

```python
# Enable automatic debugger
%pdb on

# Run code that might fail
try:
    bad_request = AnalysisRequest(pillars={})
    result = analysis_engine.analyze(bad_request)
except Exception as e:
    print(f"Error: {e}")
    %debug  # Enter debugger
```

---

## IPython Magic Commands

### Introspection

```python
# Object info
obj?                    # Show docstring and info
obj??                   # Show source code
%pdoc obj               # Print docstring
%pfile obj              # Show source file

# Variable listing
%who                    # List variables
%whos                   # List with details
%who_ls                 # List as Python list
```

### Execution

```python
# Timing
%time stmt              # Time single execution
%timeit stmt            # Time multiple runs
%prun stmt              # Profile execution

# Running code
%run script.py          # Run Python script
%load script.py         # Load script into cell
%paste                  # Paste clipboard
%cpaste                 # Paste with prompts
```

### Debugging

```python
%debug                  # Enter debugger
%pdb on                 # Auto-debug on exception
%pdb off                # Disable auto-debug
%tb                     # Print traceback
```

### History

```python
%history                # Show command history
%history -n 1-10        # Show commands 1-10
%save file.py 1-10      # Save commands to file
%recall 5               # Recall command 5
```

### System

```python
%pwd                    # Print working directory
%cd path                # Change directory
%ls                     # List files
%env                    # Show environment vars
%pip install pkg        # Install package
```

---

## Running Scripts

### Script Mode

Create a test script:

```python
# test_analysis.py
print("Testing analysis engine...")

# Use devshell objects
result = analysis_engine.analyze(sample_request)

print(f"Strength: {result.strength.level}")
print(f"Ten Gods: {result.ten_gods.summary}")

# Access container
print(f"Container singletons: {len(container._singletons)}")

print("✅ All tests passed!")
```

Run with devshell context:

```bash
python scripts/devshell.py --script test_analysis.py
```

**Output:**
```
Loading analysis-service...
Loading common utilities...
Loading sample data...
Running script: test_analysis.py

Testing analysis engine...
Strength: 신강
Ten Gods: {'비견': 2, '식신': 1, '정재': 1}
Container singletons: 2
✅ All tests passed!

✅ Script completed successfully
```

---

## Advanced Usage

### Custom Namespace

```python
# Add your own objects to namespace
my_data = load_custom_data()
my_engine = create_custom_engine()

# They're now available in shell
print(my_data)
result = my_engine.process()
```

### Service-Specific Shells

```bash
# Analysis service (default)
python scripts/devshell.py --service analysis

# Astro service (future)
python scripts/devshell.py --service astro

# Pillars service (future)
python scripts/devshell.py --service pillars
```

### Integration with pytest

```python
# test_interactive.py
def test_with_devshell():
    """Run interactive debugging session."""
    import subprocess
    result = subprocess.run(
        ["python", "scripts/devshell.py", "--script", "debug_test.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
```

---

## Troubleshooting

### Issue: Import Errors

**Problem:**
```
ImportError: cannot import name 'AnalysisEngine'
```

**Solution:**
```bash
# Ensure saju-common is installed
pip install -e services/common

# Check Python path
python -c "import sys; print(sys.path)"
```

### Issue: IPython Not Found

**Problem:**
```
⚠️  IPython not available, using standard Python REPL
```

**Solution:**
```bash
# Install IPython
pip install ipython

# Or use standard REPL
python scripts/devshell.py  # Still works, just less features
```

### Issue: Sample Data Fails

**Problem:**
```
⚠️  Could not create sample request: ...
```

**Solution:**
- Check that analysis-service is properly installed
- Verify models are importable
- Sample data is optional, you can create your own

### Issue: Analysis Service Import Fails

**Problem:**
```
⚠️  Failed to load analysis-service: Policy file not found: climate_map_v1.json
```

**Solution:**
- This is expected until Task 5 (Pydantic Settings) is complete
- Ensure `sitecustomize.py` is present at repo root
- The devshell will still work, but some features will be limited
- See `docs/SITECUSTOMIZE_RETIREMENT_PLAN.md` for details

### Issue: Policy File Not Found

**Problem:**
```
FileNotFoundError: Policy file not found: ...
```

**Solution:**
```bash
# Ensure you're in repo root
cd /path/to/saju-engine

# Or set policy root
export SAJU_POLICY_ROOT=$(pwd)

# Then run devshell
python scripts/devshell.py
```

---

## Tips & Tricks

### Tip 1: Quick Reload

```python
# Reload changed modules
%load_ext autoreload
%autoreload 2

# Now changes to .py files auto-reload
```

### Tip 2: Save Session

```python
# Save your session
%history -f my_session.py

# Reload later
%run my_session.py
```

### Tip 3: Pretty Print

```python
# Install rich for pretty printing
%pip install rich

from rich import print as rprint
rprint(result)  # Colored, formatted output
```

### Tip 4: Export Results

```python
# Export to JSON
import json
with open("result.json", "w") as f:
    json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)

# Export to CSV
import pandas as pd
df = pd.DataFrame([result.model_dump()])
df.to_csv("result.csv", index=False)
```

### Tip 5: Batch Testing

```python
# Test multiple cases
test_cases = [
    ("庚辰", "乙酉", "乙亥", "辛巳"),
    ("甲子", "丙寅", "戊辰", "庚午"),
    # ... more cases
]

results = []
for year, month, day, hour in test_cases:
    request = AnalysisRequest(
        pillars={
            "year": PillarInput(pillar=year),
            "month": PillarInput(pillar=month),
            "day": PillarInput(pillar=day),
            "hour": PillarInput(pillar=hour),
        },
        options={"birth_dt": "2000-01-01T12:00:00+09:00"}
    )
    result = analysis_engine.analyze(request)
    results.append({
        "pillars": f"{year}{month}{day}{hour}",
        "strength": result.strength.level,
        "score": result.strength_details.total,
    })

# Analyze results
import pandas as pd
df = pd.DataFrame(results)
print(df.describe())
```

---

## Configuration

### Environment Variables

```bash
# Set policy root
export SAJU_POLICY_ROOT=/path/to/policies

# Set Python path
export PYTHONPATH=/path/to/saju-engine:$PYTHONPATH

# Disable banner
export DEVSHELL_NO_BANNER=1
```

### IPython Config

Create `~/.ipython/profile_default/ipython_config.py`:

```python
# Auto-reload modules
c.InteractiveShellApp.extensions = ['autoreload']
c.InteractiveShellApp.exec_lines = ['%autoreload 2']

# Syntax highlighting
c.TerminalInteractiveShell.highlighting_style = 'monokai'

# Confirm exit
c.TerminalInteractiveShell.confirm_exit = False
```

---

## Future Enhancements

**Planned Features:**
- [ ] Web-based notebook interface (Jupyter)
- [ ] Service-specific shells (astro, pillars)
- [ ] Pre-built test scenarios
- [ ] Performance benchmarking suite
- [ ] Visual result rendering
- [ ] Integration with debugging tools

---

**Maintainer:** Claude
**Last Updated:** 2025-11-06
**Status:** Production Ready
