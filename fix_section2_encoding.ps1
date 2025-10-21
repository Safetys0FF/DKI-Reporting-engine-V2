# Fix Section 2 encoding issue
$file = "F:\The Central Command\The Analyst Deck\Analyst 2\section_2_framework.py"
$content = Get-Content $file -Raw -Encoding UTF8
$content = $content -replace 'SECTION 2 . INVESTIGATIVE REQUIREMENTS', 'SECTION 2 - INVESTIGATIVE REQUIREMENTS'
Set-Content -Path $file -Value $content -NoNewline -Encoding UTF8
Write-Host "Section 2 encoding fixed!"

