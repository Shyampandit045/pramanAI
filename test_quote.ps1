# Single-click PowerShell verification script
$quote = "freedom of speech and of the press lay at the foundation of all democratic organisations, for without free political discussion no public education, so essential for the proper functioning of the processes of popular government, is possible."
$jsonBody = "{`"judgment_id`":`"sc-1950-594`",`"submitted_quote`":`"$quote`"}"

Write-Host "Sending verification request to Praman AI backend..." -ForegroundColor Cyan
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/verify" -Method Post -Body $jsonBody -ContentType "application/json"
    Write-Host "`n================ VERIFICATION RESULT ================" -ForegroundColor Green
    Write-Host "Status:           $($res.status)" -ForegroundColor Yellow
    Write-Host "Similarity Score: $($res.similarity_score)%" -ForegroundColor Green
    Write-Host "Case Title:       $($res.case_details.title)" -ForegroundColor White
    Write-Host "Citation:         $($res.case_details.citation)" -ForegroundColor Cyan
    Write-Host "Page Number:      Page $($res.page_number)" -ForegroundColor Magenta
    Write-Host "Quote DNA:        $($res.quote_dna.submitted.fingerprint)" -ForegroundColor Yellow
    Write-Host "Explanation:      $($res.explanation)" -ForegroundColor Gray
    Write-Host "=====================================================`n" -ForegroundColor Green
} catch {
    Write-Host "Error connecting to backend: $_" -ForegroundColor Red
    Write-Host "Ensure backend is running: python run.py" -ForegroundColor Yellow
}

