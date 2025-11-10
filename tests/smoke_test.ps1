# queuectl smoke test
Write-Host "Starting worker..."
Start-Process -FilePath "python" -ArgumentList "src\queuectl.py", "worker", "start", "--count", "1" -WindowStyle Hidden
Start-Sleep -Seconds 2

Write-Host "Enqueue success job"
python src\queuectl.py enqueue '{"id":"job1","command":"echo hello"}'

Write-Host "Enqueue fail job"
python src\queuectl.py enqueue '{"id":"job2","command":"false"}'

Write-Host "Waiting for retries..."
Start-Sleep -Seconds 15

Write-Host "Status:"
python src\queuectl.py status

Write-Host "DLQ list:"
python src\queuectl.py dlq list
