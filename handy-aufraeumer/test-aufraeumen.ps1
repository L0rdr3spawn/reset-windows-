# Testet den Aufraeum-Prompt gegen den laufenden Server (deutsch, englisch, gemischt)
param([string]$PromptDatei = "$PSScriptRoot\prompt.txt")
$vorlage = [IO.File]::ReadAllText($PromptDatei, [Text.Encoding]::UTF8)
$faelle = @(
  'also ähm ich wollte nur kurz sagen dass das meeting morgen um zehn uhr ist und äh bitte bring den laptop mit und das quarterly review deck danke',
  'hey um can you send me the report by friday uh i need it for the client call at three thirty',
  'kannst du mal den pull request reviewen der fixt den bug im login flow also wenn der token expired ist komma dann crasht die app punkt',
  'ich hab ähm fünfundzwanzig prozent mehr umsatz gemacht als letztes jahr fragezeichen nein ausrufezeichen'
)
foreach ($t in $faelle) {
  $body = @{ model='qwen3-4b'; messages=@(@{role='user'; content=$vorlage.Replace('${output}', $t)}); temperature=0.1 } | ConvertTo-Json -Depth 5
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $r = Invoke-RestMethod http://127.0.0.1:8091/v1/chat/completions -Method Post -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
  "[{0,5} ms] {1}" -f $sw.ElapsedMilliseconds, $r.choices[0].message.content.Trim()
}
