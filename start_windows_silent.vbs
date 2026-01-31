' txt-snippets launcher for Windows (No Command Prompt window)
' Double-click this file to start txt-snippets silently

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get script directory
strScriptPath = WScript.ScriptFullName
strScriptDir = objFSO.GetParentFolderName(strScriptPath)

' Change to script directory
objShell.CurrentDirectory = strScriptDir

' Check if venv exists, if not run the bat file first (will show console once)
If Not objFSO.FolderExists(strScriptDir & "\.venv") Then
    objShell.Run "cmd /c start_windows.bat", 1, True
Else
    ' Run Python silently using pythonw (no console window)
    ' First try pythonw, fallback to python with hidden window
    strVenvPython = strScriptDir & "\.venv\Scripts\pythonw.exe"
    strVenvPythonFallback = strScriptDir & "\.venv\Scripts\python.exe"
    strMainPy = strScriptDir & "\main.py"
    
    If objFSO.FileExists(strVenvPython) Then
        objShell.Run """" & strVenvPython & """ """ & strMainPy & """", 0, False
    Else
        objShell.Run """" & strVenvPythonFallback & """ """ & strMainPy & """", 0, False
    End If
End If
