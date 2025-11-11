for ($i = 1; $i -le 30; $i++) {
    # Generate a random sleep duration between 0 and 450 milliseconds (0.05 * 0–9)
    $random = Get-Random -Minimum 0 -Maximum 10
    $sleepMs = 50 * $random  # 50 ms * random 0–9

    Start-Sleep -Milliseconds $sleepMs

    # Generate a random result between 0 and 9
    $result = Get-Random -Minimum 0 -Maximum 10

    Write-Output "Finished task $i. Random Result: $result"
}

Write-Output "All done!"
exit 0
