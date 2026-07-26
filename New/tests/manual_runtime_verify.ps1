$ErrorActionPreference='Stop'

function Parse-NDJson([string]$content) {
  $lines = $content -split "`n" | Where-Object { $_.Trim() -ne '' }
  $packets = @()
  foreach ($l in $lines) {
    try { $packets += ($l | ConvertFrom-Json) } catch {}
  }
  return ,$packets
}

function Decode-Content($content) {
  if ($content -is [byte[]]) {
    return [System.Text.Encoding]::UTF8.GetString($content)
  }
  return [string]$content
}

$session = 'manual-verify-session'
$clearBody = @{ session_id = $session } | ConvertTo-Json -Compress
Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/clear_history' -ContentType 'application/json' -Body $clearBody -UseBasicParsing | Out-Null

$body1 = @{ prompt='My favorite color is green.'; history=@(); system_prompt_name=''; use_memory=$true; session_id=$session } | ConvertTo-Json -Compress
$resp1 = Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/chat_voice_stream' -ContentType 'application/json' -Body $body1 -UseBasicParsing
$packets1 = Parse-NDJson (Decode-Content $resp1.Content)
$text1 = ($packets1 | Where-Object { $_.type -eq 'text' } | ForEach-Object { $_.content }) -join ''

$body2 = @{ prompt='What is my favorite color?'; history=@(); system_prompt_name=''; use_memory=$true; session_id=$session } | ConvertTo-Json -Compress
$resp2 = Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/chat_voice_stream' -ContentType 'application/json' -Body $body2 -UseBasicParsing
$packets2 = Parse-NDJson (Decode-Content $resp2.Content)
$text2 = ($packets2 | Where-Object { $_.type -eq 'text' } | ForEach-Object { $_.content }) -join ''

$body3 = @{ prompt='I passed my exam, I am so happy!'; history=@(); system_prompt_name=''; use_memory=$true; session_id=$session } | ConvertTo-Json -Compress
$resp3 = Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/chat_voice_stream' -ContentType 'application/json' -Body $body3 -UseBasicParsing
$packets3 = Parse-NDJson (Decode-Content $resp3.Content)
$userEmotion3 = $packets3 | Where-Object { $_.type -eq 'emotion' -and $_.source -eq 'user' } | Select-Object -First 1

$offSession='manual-memory-off'
Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/clear_history' -ContentType 'application/json' -Body (@{session_id=$offSession}|ConvertTo-Json -Compress) -UseBasicParsing | Out-Null
$bodyOff = @{ prompt='Remember this should not persist'; history=@(); system_prompt_name=''; use_memory=$false; session_id=$offSession } | ConvertTo-Json -Compress
Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/chat_voice_stream' -ContentType 'application/json' -Body $bodyOff -UseBasicParsing | Out-Null

$sessionA='clear-A'
$sessionB='clear-B'
Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/clear_history' -ContentType 'application/json' -Body (@{session_id=$sessionA}|ConvertTo-Json -Compress) -UseBasicParsing | Out-Null
Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/clear_history' -ContentType 'application/json' -Body (@{session_id=$sessionB}|ConvertTo-Json -Compress) -UseBasicParsing | Out-Null
Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/chat_voice_stream' -ContentType 'application/json' -Body (@{prompt='A only'; history=@(); system_prompt_name=''; use_memory=$true; session_id=$sessionA}|ConvertTo-Json -Compress) -UseBasicParsing | Out-Null
Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/chat_voice_stream' -ContentType 'application/json' -Body (@{prompt='B only'; history=@(); system_prompt_name=''; use_memory=$true; session_id=$sessionB}|ConvertTo-Json -Compress) -UseBasicParsing | Out-Null
Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8000/clear_history' -ContentType 'application/json' -Body (@{session_id=$sessionA}|ConvertTo-Json -Compress) -UseBasicParsing | Out-Null

Write-Output 'RESULT_MSG1_START'
Write-Output $text1
Write-Output 'RESULT_MSG1_END'
Write-Output 'RESULT_MSG2_START'
Write-Output $text2
Write-Output 'RESULT_MSG2_END'
Write-Output ('RESULT_MSG2_HAS_GREEN=' + ($text2.ToLower().Contains('green')))
if ($userEmotion3) {
  Write-Output ('RESULT_EMOTION_USER=' + $userEmotion3.emotion)
  Write-Output ('RESULT_EMOTION_SOURCE=' + $userEmotion3.source)
} else {
  Write-Output 'RESULT_EMOTION_USER=NONE'
}
