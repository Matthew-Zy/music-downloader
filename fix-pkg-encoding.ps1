#
# Powershell
# Me when the shell suddenly has power
# Run with:
# powershell -File fix-pkg-encoding.ps1
#

$project_dir = $PSScriptRoot
$target_file="${project_dir}\.venv\Lib\site-packages\nodriver\cdp\network.py"

$lineNumberToDelete = 1345
$index = $lineNumberToDelete - 1

$lines = Get-Content -Path $target_file

if ($index -lt $lines.Count -and $lines[$index].TrimStart() -like '#*') {
    $lines[0..($index - 1) + ($index + 1)..($lines.Count - 1)] | Set-Content -Path $target_file
    Write-Host "Line $lineNumberToDelete was a comment and has been deleted."
} else {
    Write-Host "Line $lineNumberToDelete did not start with a # or does not exist. No changes made."
}
