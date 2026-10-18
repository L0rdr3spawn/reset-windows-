# Demo-Zugaenge fuer die beiden Beta-Tester eintragen (verdeckte Eingabe).
# Gespeichert in ~\.openclaw\secrets\betatest-zugaenge.json, nur fuer Ihren Windows-Benutzer lesbar.
# Bitte NUR Zugaenge der Demo-Instanz verwenden (vom Demo-Inhaber ausgegeben), nie echte Konten.
$dir = "$env:USERPROFILE\.openclaw\secrets"
New-Item -ItemType Directory -Force $dir | Out-Null
$datei = "$dir\betatest-zugaenge.json"
function Frage($rolle) {
    Write-Host ""
    Write-Host "Zugang fuer $rolle (leer lassen = keiner):" -ForegroundColor Cyan
    $u = Read-Host "  Benutzername"
    if (-not $u) { return $null }
    $s = Read-Host "  Passwort" -AsSecureString
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    $p = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b)
    return @{ benutzer = $u.Trim(); passwort = $p }
}
Write-Host "=== Demo-Zugaenge fuer den Beta-Test ===" -ForegroundColor Cyan
Write-Host "Tipp: Tester A prueft Bedienung und Aussehen -> z. B. ein Lehrkraft- oder Schulleitungs-Zugang."
Write-Host "      Tester B prueft vor allem Code, klickt aber zur Kontrolle auch -> z. B. ein Schueler- oder Eltern-Zugang."
$z = @{ tester_a = (Frage "Tester A"); tester_b = (Frage "Tester B") }
$json = $z | ConvertTo-Json
[IO.File]::WriteAllText($datei, $json, (New-Object System.Text.UTF8Encoding $false))
icacls $datei /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null
Write-Host ""
Write-Host "Gespeichert (nur fuer Sie lesbar): $datei" -ForegroundColor Green
Read-Host "Enter zum Schliessen"
