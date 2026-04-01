import os
import zipfile

def zip_project(source_dir, output_filename):
    zip_basename = os.path.basename(output_filename)
    exclude_dirs = {'venv', '.git', '__pycache__', 'node_modules', '.venv',
                    'staticfiles', '.vscode', 'env', 'tmp', 'db.sqlite3', '.env'}

    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Remove excluded directories in-place so os.walk skips them
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                # Skip compiled, zip, log, and sensitive files
                if file.endswith(('.pyc', '.log')) or file in (zip_basename, 'db.sqlite3', '.env', 'nul'):
                    continue

                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)

    print(f"[OK] Successfully packaged: {output_filename}")

if __name__ == "__main__":
    source = r'C:\PrairieWealth'
    output = r'C:\PrairieWealth\prairiewealth_production.zip'
    zip_project(source, output)
