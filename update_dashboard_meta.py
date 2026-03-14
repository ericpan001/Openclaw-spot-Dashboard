#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUT = BASE_DIR / 'dashboard_meta.json'

def main():
    model = 'unknown'
    try:
        raw = subprocess.check_output(['openclaw', 'status', '--json'], text=True, timeout=20)
        data = json.loads(raw)
        recent = (((data.get('sessions') or {}).get('recent')) or [])
        if recent:
            model = recent[0].get('model') or model
        defaults = (((data.get('sessions') or {}).get('defaults')) or {})
        default_model = defaults.get('model')
        payload = {
            'currentModel': model,
            'defaultModel': default_model,
            'runtimeVersion': data.get('runtimeVersion'),
            'updatedAt': data.get('sessions', {}).get('recent', [{}])[0].get('updatedAt') if recent else None
        }
    except Exception as e:
        payload = {
            'currentModel': model,
            'defaultModel': None,
            'runtimeVersion': None,
            'error': str(e)
        }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    main()
