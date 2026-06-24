# מריץ פעם אחת אחרי git clone — מתקין את זיכרון הפרויקטים ב-Claude Code
$repoPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectSlug = $repoPath -replace '\\', '-' -replace ':', '-' -replace '^-', ''
$targetPath = "$env:USERPROFILE\.claude\projects\$projectSlug\memory"

New-Item -ItemType Directory -Force -Path $targetPath | Out-Null
Copy-Item "$repoPath\.claude-memory\*" $targetPath -Force

Write-Host "Done! Memory installed to: $targetPath"
