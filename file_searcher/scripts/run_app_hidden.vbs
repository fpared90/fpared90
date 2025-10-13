Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
sh.CurrentDirectory = root
cmd = "cmd /c py -3 -m file_searcher || python -m file_searcher"
On Error Resume Next
sh.Run cmd, 7, False
WScript.Quit 0
