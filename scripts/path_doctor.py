#!/usr/bin/env python3
import os
import glob
import re

def fix_shell(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    if 'WORKSPACE_ROOT' in content: return

    # Shell Root Detection
    # If in bin/, root is one level up. If in skills/*/bin/, root is 3 levels up.
    # We'll use a robust one-liner that handles both if possible, 
    # but since these are in bin/ we can be specific.
    root_detection = """
# --- Physical Path Hardening (Nexus 2.0) ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [[ "$SCRIPT_DIR" == *"/skills/"* ]]; then
    WORKSPACE_ROOT="$( cd "$SCRIPT_DIR/../../.." && pwd )"
else
    WORKSPACE_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
fi
"""
    
    # Insert after shebang
    lines = content.split('\n')
    lines.insert(1, root_detection)
    new_content = '\n'.join(lines)
    
    # Replace ./bin/ with $WORKSPACE_ROOT/bin/
    new_content = new_content.replace('./bin/', '$WORKSPACE_ROOT/bin/')
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    print(f"[+] Hardened Shell: {file_path}")

def fix_python(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    if 'WORKSPACE_ROOT' in content: return

    root_detection = """
# --- Physical Path Hardening (Nexus 2.0) ---
import os
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if "/skills/" in _SCRIPT_DIR:
    WORKSPACE_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "../../.."))
else:
    WORKSPACE_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
"""
    
    lines = content.split('\n')
    lines.insert(1, root_detection)
    new_content = '\n'.join(lines)
    
    # Replace "./bin/" strings in python
    new_content = new_content.replace('"./bin/"', 'os.path.join(WORKSPACE_ROOT, "bin") + "/"')
    new_content = new_content.replace("'./bin/'", 'os.path.join(WORKSPACE_ROOT, "bin") + "/"')
    # Special case for subprocess lists: "./bin/agent-reach" -> os.path.join(WORKSPACE_ROOT, "bin/agent-reach")
    new_content = re.sub(r'["\']\./bin/(\w+-\w+|\w+)["\']', r'os.path.join(WORKSPACE_ROOT, "bin/\1")', new_content)

    with open(file_path, 'w') as f:
        f.write(new_content)
    print(f"[+] Hardened Python: {file_path}")

if __name__ == "__main__":
    scripts = glob.glob("bin/*")
    for s in scripts:
        if os.path.isdir(s): continue
        with open(s, 'r') as f:
            first_line = f.readline()
        
        if 'python' in first_line:
            fix_python(s)
        elif 'bash' in first_line or 'sh' in first_line:
            fix_shell(s)
