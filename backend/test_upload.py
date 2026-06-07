"""
Test upload-predict endpoint.
Run: cd edu-governance-platform/backend && python test_upload.py
"""
import sys; sys.path.insert(0, '.')
import os
import requests
import tempfile

BASE = 'http://localhost:8000/api/v1'

# 1. Download template
print("1. Downloading template...")
r = requests.get(f'{BASE}/dropout/template')
print(f"   Status: {r.status_code}, Size: {len(r.content)} bytes")

# Save to temp
tmpdir = tempfile.gettempdir()
template_path = os.path.join(tmpdir, 'test_template.xlsx')
with open(template_path, 'wb') as f:
    f.write(r.content)
print(f"   Saved to: {template_path}")

# 2. Upload the same template back
print("\n2. Uploading template back...")
with open(template_path, 'rb') as f:
    r2 = requests.post(
        f'{BASE}/dropout/upload-predict',
        files={'file': ('test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    )
print(f"   Status: {r2.status_code}")
if r2.status_code == 200:
    output_path = os.path.join(tmpdir, 'test_output.xlsx')
    with open(output_path, 'wb') as f:
        f.write(r2.content)
    print(f"\n✅ SUCCESS! Status: {r2.status_code}")
    print(f"   Output saved to: {output_path}")
    print(f"   Size: {len(r2.content)} bytes")
    print(f"   Content-Type: {r2.headers.get('Content-Type', 'N/A')}")
else:
    print(f"\n❌ FAILED! Status: {r2.status_code}")
    print(f"   Error: {r2.text}")
