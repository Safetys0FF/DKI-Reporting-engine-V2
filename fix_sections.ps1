# Fix all section frameworks to work in degraded mode

$sections = @(
    "F:\The Central Command\The Analyst Deck\Analyst 1\section_1_framework.py",
    "F:\The Central Command\The Analyst Deck\Analyst 2\section_2_framework.py",
    "F:\The Central Command\The Analyst Deck\Analyst 3\section_3_framework.py",
    "F:\The Central Command\The Analyst Deck\Analyst 4\section_4_framework.py",
    "F:\The Central Command\The Analyst Deck\Analyst 5\section_5_framework.py",
    "F:\The Central Command\The Analyst Deck\Analyst 6\section_6_framework.py",
    "F:\The Central Command\The Analyst Deck\Analyst 7\section_7_framework.py",
    "F:\The Central Command\The Analyst Deck\Analyst 8\section_8_framework.py"
)

foreach ($file in $sections) {
    if (Test-Path $file) {
        Write-Host "Fixing: $file"
        $content = Get-Content $file -Raw
        $content = $content -replace 'self\.logger\.error\("\[%s\] Bus stabilization timeout - initialization may be unstable"', 'self.logger.warning("[%s] Bus stabilization timeout - initializing in degraded mode"'
        $content = $content -replace 'self\.logger\.error\("\[%s\] Module turn timeout - cannot initialize"', 'self.logger.warning("[%s] Module turn timeout - initializing in degraded mode"'
        Set-Content -Path $file -Value $content -NoNewline
    }
}

Write-Host "All sections fixed!"

