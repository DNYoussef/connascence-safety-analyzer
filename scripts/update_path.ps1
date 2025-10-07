$wrapperDir = "C:\Users\17175\AppData\Local\Programs"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$wrapperDir*") {
    $newPath = "$wrapperDir;" + $currentPath
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Output "PATH updated successfully. Added: $wrapperDir"
} else {
    Write-Output "PATH already contains: $wrapperDir"
}

Write-Output "`nCurrent PATH entries:"
$currentPath -split ';' | Select-Object -First 5
