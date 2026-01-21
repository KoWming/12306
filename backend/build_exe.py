import PyInstaller.__main__
import os
import shutil

# Clean previous build
if os.path.exists('backend/dist'):
    shutil.rmtree('backend/dist')
if os.path.exists('backend/build'):
    shutil.rmtree('backend/build')

# Run PyInstaller
PyInstaller.__main__.run([
    'backend/run_server.py',
    '--name=12306-backend',
    '--onedir',
    '--noconfirm',
    '--clean',
    '--distpath=backend/dist',
    '--workpath=backend/build',
    '--specpath=backend',
    # Include the app package. 
    # Since run_server imports main, and main imports app, PyInstaller should find it.
    # Hidden imports for Uvicorn
    '--hidden-import=uvicorn.logging',
    '--hidden-import=uvicorn.loops',
    '--hidden-import=uvicorn.loops.auto',
    '--hidden-import=uvicorn.protocols',
    '--hidden-import=uvicorn.protocols.http',
    '--hidden-import=uvicorn.protocols.http.auto',
    '--hidden-import=uvicorn.protocols.websockets',
    '--hidden-import=uvicorn.protocols.websockets.auto',
    '--hidden-import=uvicorn.lifespan',
    '--hidden-import=uvicorn.lifespan.on',
])

print("Build complete. Copying data files...")

# Copy data folder structure (empty or with initial files)
# The config ensures directories, but we should ship assets like station_name.js
src_data_assets = 'backend/data/assets'
dst_data_assets = 'backend/dist/12306-backend/data/assets'

if not os.path.exists(dst_data_assets):
    os.makedirs(dst_data_assets)
    
if os.path.exists(src_data_assets):
    # Copy files
    for item in os.listdir(src_data_assets):
        s = os.path.join(src_data_assets, item)
        d = os.path.join(dst_data_assets, item)
        if os.path.isfile(s):
            shutil.copy2(s, d)

print("Data files copied.")
