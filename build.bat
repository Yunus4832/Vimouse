.\venv\Scripts\pyinstaller.exe --clean --noconfirm --onedir --windowed --name "vimouse" --icon "./logo.ico"   --add-data "./src/utils;utils/" --paths "./venv/Lib/site-packages" --distpath "./dist/" --hidden-import=json --debug=imports  -F "./src/vimouse.py"
