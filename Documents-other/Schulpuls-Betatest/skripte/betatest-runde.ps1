# Beta-Test des Schulmanagers mit drei OpenClaw-Agenten (sm-admin, sm-tester-a, sm-tester-b).
# Ablauf je Bereich:
#   1. Kopie vom Server holen (immer neuester Stand beim Admin)
#   2. Admin teilt den Bereich in Auftrag A (Bedienung/Aussehen in der Demo) und Auftrag B (Code)
#   3. Tester A und Tester B arbeiten gleichzeitig und schreiben je einen Bericht
#   4. Gegenpruefung ueber Kreuz: B prueft den Bericht von A, A prueft den Bericht von B
#   5. Admin schreibt aus allem einen Update-Patch -> Dokumente\Schulpuls-Betatest\patches
# Aufruf:
#   betatest-runde.ps1                    naechster offener Bereich
#   betatest-runde.ps1 -Bereich nachrichten
#   betatest-runde.ps1 -Alle              alle offenen Bereiche nacheinander, bis alles durch ist
#   betatest-runde.ps1 -Neu               Fortschritt zuruecksetzen (alle Bereiche wieder offen)
param(
    [string]$Bereich = "",
    [switch]$Alle,
    [switch]$Neu,
    [switch]$OhneKopie,
    [int]$TimeoutSek = 1200
)
$ErrorActionPreference = "Stop"
$Basis   = Split-Path $PSScriptRoot -Parent                     # ...\Documents\Schulpuls-Betatest
$N       = "C:\Users\reiss\Programme\node-v24.22.0-win-x64"
$OC      = "$N\node_modules\openclaw\openclaw.mjs"
$Atlas   = "C:\Users\reiss\Documents\claude\schulpuls-atlas"
$Kopie   = "$env:USERPROFILE\.openclaw\workspace-sm-admin\schulmanager-kopie"
$Demo    = "https://schulmanager-demo.l0rdr3spawn.duckdns.org:10489"
$Zugaenge = "$env:USERPROFILE\.openclaw\secrets\betatest-zugaenge.json"
$StatusDatei = "$Basis\status.json"
$Arbeit  = "$Basis\.arbeit"
$Log     = "$Basis\verlauf.log"
New-Item -ItemType Directory -Force "$Basis\patches", "$Basis\berichte", $Arbeit | Out-Null
$utf8 = New-Object System.Text.UTF8Encoding $false

function Log($text) {
    $zeile = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $text"
    Write-Host $zeile
    [IO.File]::AppendAllText($Log, $zeile + "`r`n", $utf8)
}
function Schreibe($pfad, $text) { [IO.File]::WriteAllText($pfad, $text, $utf8) }
function Lies($pfad) { if (Test-Path $pfad) { [IO.File]::ReadAllText($pfad, $utf8) } else { "" } }

# --- Vorbedingungen ------------------------------------------------------------
if (-not (Get-NetTCPConnection -LocalPort 18789 -State Listen -ErrorAction SilentlyContinue)) {
    throw "OpenClaw laeuft nicht. Bitte zuerst 'OpenClaw starten' auf dem Desktop ausfuehren."
}

# --- Bereichsliste aus dem Atlas (INDEX.md) --------------------------------------
function Lade-Status {
    $bereiche = @()
    foreach ($z in (Get-Content "$Atlas\INDEX.md" -Encoding UTF8)) {
        if ($z -match '^\| \[(?<titel>[^\]]+)\]\(features/(?<slug>[a-z0-9\-]+)\.md\) \| (?<zweck>[^|]*)\|') {
            $bereiche += [pscustomobject]@{ slug = $Matches.slug; titel = $Matches.titel; zweck = $Matches.zweck.Trim(); status = "offen"; zuletzt = ""; patch = "" }
        }
    }
    if ((Test-Path $StatusDatei) -and -not $Neu) {
        $alt = (Lies $StatusDatei) | ConvertFrom-Json
        foreach ($b in $bereiche) {
            $a = $alt | Where-Object { $_.slug -eq $b.slug } | Select-Object -First 1
            if ($a) { $b.status = $a.status; $b.zuletzt = $a.zuletzt; $b.patch = $a.patch }
        }
    }
    return ,$bereiche
}
function Speichere-Status($bereiche) { Schreibe $StatusDatei ($bereiche | ConvertTo-Json -Depth 4) }

# --- Agent aufrufen (mehrere gleichzeitig moeglich) -----------------------------
function Starte-Agent($agent, $sitzung, $nachricht, $name) {
    $msg = "$Arbeit\$name.msg.txt"; $out = "$Arbeit\$name.out.txt"; $err = "$Arbeit\$name.err.txt"
    Schreibe $msg $nachricht
    $argumente = "`"$OC`" agent --agent $agent --session-id $sitzung --timeout $TimeoutSek --message-file `"$msg`""
    $p = Start-Process -FilePath "$N\node.exe" -ArgumentList $argumente -NoNewWindow -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    return [pscustomobject]@{ p = $p; out = $out; err = $err; name = $name }
}
function Warte-Agent($lauf) {
    $lauf.p.WaitForExit()
    $text = (Lies $lauf.out).Trim()
    if (-not $text) { $text = "(keine Antwort; Fehler: " + ((Lies $lauf.err).Trim() -split "`n" | Select-Object -Last 3) -join " " + ")" }
    return $text
}

# Fehlgeschlagenen Lauf (z. B. "Couldn't connect to the AI service" bei Last) einmal allein wiederholen
function Mit-Wiederholung($text, $agent, $sitzung, $nachricht, $name) {
    if ($text -notlike "(keine Antwort*") { return $text }
    Log "Wiederhole $name (erster Versuch ohne Antwort)"
    Start-Sleep 20
    return Warte-Agent (Starte-Agent $agent "$sitzung-2" $nachricht "$name-2")
}

function Bereichs-Kontext($slug) {
    $f = Lies "$Atlas\features\$slug.md"
    # Nur das Noetigste: Zweck, Dateien, Frontend-Routen (gekuerzt, damit Gemma Platz hat)
    $teile = @()
    foreach ($kopf in "Zweck", "Dateien", "Frontend") {
        $m = [regex]::Match($f, "(?ms)^## [^\n]*$kopf[^\n]*\n(.*?)(?=^## |\z)")
        if ($m.Success) { $teile += "## $kopf`n" + $m.Groups[1].Value.Trim() }
    }
    $text = ($teile -join "`n`n")
    if ($text.Length -gt 3500) { $text = $text.Substring(0, 3500) + "`n(gekuerzt)" }
    return $text
}

function Login-Hinweis($rolle) {
    if (-not (Test-Path $Zugaenge)) {
        return "Fuer die Demo sind noch keine Zugaenge hinterlegt. Pruefen Sie nur oeffentliche Seiten (Anmeldeseite, Passwort vergessen, Darstellung am Handy) und stuetzen Sie sich sonst auf den Code der Frontend-Seiten in der Kopie."
    }
    $z = (Lies $Zugaenge) | ConvertFrom-Json
    $k = $z.$rolle
    if (-not $k) { return "Fuer Ihre Rolle ist kein Demo-Zugang hinterlegt. Pruefen Sie oeffentliche Seiten und den Frontend-Code." }
    return "Demo-Zugang (nur fuer diese Pruefung, nie weitergeben, nie in den Bericht schreiben): Benutzername $($k.benutzer) / Passwort $($k.passwort). Melden Sie sich damit in der Demo an."
}

# --- Eine Runde fuer einen Bereich ----------------------------------------------
function Runde($b) {
    $stempel = Get-Date -Format "yyyy-MM-dd_HHmm"
    $id = "$($b.slug)-$(Get-Date -Format 'MMddHHmm')"
    $kontext = Bereichs-Kontext $b.slug
    Log "=== Bereich '$($b.titel)' ($($b.slug)) beginnt"

    # 1. Admin teilt auf
    $auftrag = @"
Neuer Pruefbereich: $($b.titel)
Zweck: $($b.zweck)
Code-Kopie: $Kopie
Demo: $Demo

Ausschnitt aus der internen Bereichsuebersicht:
$kontext

Teilen Sie diesen Bereich in genau zwei Pruefauftraege. Antworten Sie NUR im Format:
AUFTRAG A: ...
AUFTRAG B: ...
"@
    $r = Warte-Agent (Starte-Agent "sm-admin" "bt-$id-plan" $auftrag "$id-admin-plan")
    $aA = [regex]::Match($r, "(?s)AUFTRAG A:\s*(.+?)(?=AUFTRAG B:|\z)").Groups[1].Value.Trim()
    $aB = [regex]::Match($r, "(?s)AUFTRAG B:\s*(.+)$").Groups[1].Value.Trim()
    if (-not $aA) { $aA = "Pruefen Sie in der Demo alle Seiten des Bereichs '$($b.titel)' auf Bedienbarkeit, Verstaendlichkeit, Aussehen, Handy-Darstellung und Sie-Form." }
    if (-not $aB) { $aB = "Pruefen Sie in der Code-Kopie die Dateien des Bereichs '$($b.titel)' auf Aufbau, Modularitaet, Doppelungen, Fehlerbehandlung und Verstoesse gegen die Projektregeln." }
    Log "Admin-Auftraege: A=$($aA.Length) Zeichen, B=$($aB.Length) Zeichen"

    # 2. Beide Tester gleichzeitig
    $mA = @"
Ihr Pruefauftrag (Bereich $($b.titel)), Sie sind Tester A:
$aA

$(Login-Hinweis 'tester_a')
Demo: $Demo
Code-Kopie: $Kopie
Dateien und Seiten des Bereichs:
$kontext

Schreiben Sie Ihren Bericht im Berichtsformat aus Ihrer Rolle.
"@
    $mB = @"
Ihr Pruefauftrag (Bereich $($b.titel)), Sie sind Tester B:
$aB

$(Login-Hinweis 'tester_b')
Demo: $Demo
Code-Kopie: $Kopie
Dateien und Seiten des Bereichs:
$kontext

Schreiben Sie Ihren Bericht im Berichtsformat aus Ihrer Rolle.
"@
    $tA = Starte-Agent "sm-tester-a" "bt-$id-a" $mA "$id-bericht-a"
    $tB = Starte-Agent "sm-tester-b" "bt-$id-b" $mB "$id-bericht-b"
    $berichtA = Mit-Wiederholung (Warte-Agent $tA) "sm-tester-a" "bt-$id-a" $mA "$id-bericht-a"
    $berichtB = Mit-Wiederholung (Warte-Agent $tB) "sm-tester-b" "bt-$id-b" $mB "$id-bericht-b"
    Log "Berichte da (A: $($berichtA.Length), B: $($berichtB.Length) Zeichen)"

    # 3. Gegenpruefung ueber Kreuz (gleichzeitig)
    $mGA = @"
Pruefen Sie den folgenden Bericht von Tester A kritisch (Bereich $($b.titel)). Kontrollieren Sie jede Behauptung, wo moeglich in der Demo oder in der Code-Kopie ($Kopie).
Antworten Sie im Format Gegenpruefung aus Ihrer Rolle.

----- BERICHT TESTER A -----
$berichtA
"@
    $mGB = @"
Pruefen Sie den folgenden Bericht von Tester B kritisch (Bereich $($b.titel)). Kontrollieren Sie jede Behauptung, wo moeglich in der Code-Kopie ($Kopie) oder in der Demo.
Antworten Sie im Format Gegenpruefung aus Ihrer Rolle.

----- BERICHT TESTER B -----
$berichtB
"@
    $gB = Starte-Agent "sm-tester-b" "bt-$id-b-gegen" $mGA "$id-gegen-a"
    $gA = Starte-Agent "sm-tester-a" "bt-$id-a-gegen" $mGB "$id-gegen-b"
    $gegenA = Mit-Wiederholung (Warte-Agent $gB) "sm-tester-b" "bt-$id-b-gegen" $mGA "$id-gegen-a"
    $gegenB = Mit-Wiederholung (Warte-Agent $gA) "sm-tester-a" "bt-$id-a-gegen" $mGB "$id-gegen-b"
    Log "Gegenpruefungen da"

    # 4. Admin schreibt den Update-Patch
    $patch = Warte-Agent (Starte-Agent "sm-admin" "bt-$id-patch" @"
Schreiben Sie jetzt den Update-Patch fuer den Bereich $($b.titel) im Format aus Ihrer Rolle. Beginnen Sie direkt mit "# Update-Patch", ohne Vorrede und ohne Schlusswort.
Keine Grossumbauten vorschlagen, wenn ein kleiner gezielter Fix reicht. Pruefen Sie jeden Befund selbst in der Kopie, bevor Sie ihn uebernehmen.
Nur bestaetigte Befunde, zweifelhafte als "pruefen", verworfene weglassen. Diffs nur, wenn Sie die Stelle in der Kopie ($Kopie) wirklich gelesen haben.

----- BERICHT TESTER A -----
$berichtA

----- GEGENPRUEFUNG VON A DURCH B -----
$gegenA

----- BERICHT TESTER B -----
$berichtB

----- GEGENPRUEFUNG VON B DURCH A -----
$gegenB
"@ "$id-patch")
    $stand = (Lies "$Kopie\STAND.txt").Trim()

    # 5. Ablegen
    $patchDatei = "$Basis\patches\${stempel}_$($b.slug).md"
    Schreibe $patchDatei ("<!-- Beta-Test Schulmanager, Bereich: $($b.titel), erstellt $stempel. $stand -->`n`n" + $patch)
    Schreibe "$Basis\berichte\${stempel}_$($b.slug)_bericht-a.md" $berichtA
    Schreibe "$Basis\berichte\${stempel}_$($b.slug)_bericht-b.md" $berichtB
    Schreibe "$Basis\berichte\${stempel}_$($b.slug)_gegenpruefung-von-a.md" $gegenA
    Schreibe "$Basis\berichte\${stempel}_$($b.slug)_gegenpruefung-von-b.md" $gegenB
    Get-ChildItem $Arbeit -Filter "$id-*" | Remove-Item -Force -ErrorAction SilentlyContinue
    Log "Patch gespeichert: $patchDatei"
    return $patchDatei
}

# --- Hauptablauf ----------------------------------------------------------------
$status = Lade-Status
if ($Neu) { Speichere-Status $status; Log "Fortschritt zurueckgesetzt ($($status.Count) Bereiche offen)." ; if (-not $Alle -and -not $Bereich) { exit 0 } }
if (-not $OhneKopie) { & "$PSScriptRoot\kopie-holen.ps1"; Log "Server-Kopie aktualisiert." }

do {
    if ($Bereich) { $b = $status | Where-Object { $_.slug -eq $Bereich } | Select-Object -First 1
                    if (-not $b) { throw "Unbekannter Bereich '$Bereich'. Moeglich: $(($status | ForEach-Object slug) -join ', ')" } }
    else { $b = $status | Where-Object { $_.status -ne "fertig" } | Select-Object -First 1 }
    if (-not $b) { Log "Alle $($status.Count) Bereiche sind durchgeprueft. Fuer eine neue Runde: -Neu"; break }
    $b.status = "laeuft"; Speichere-Status $status
    try {
        $p = Runde $b
        $b.status = "fertig"; $b.zuletzt = (Get-Date -Format "yyyy-MM-dd HH:mm"); $b.patch = (Split-Path $p -Leaf)
    } catch {
        $b.status = "fehler"; Log "FEHLER in $($b.slug): $_"
    }
    Speichere-Status $status
    $offen = ($status | Where-Object { $_.status -ne "fertig" }).Count
    Log "Fortschritt: $($status.Count - $offen) von $($status.Count) Bereichen fertig."
    if ($Bereich) { break }
} while ($Alle)
