echo '$env:ERLANGURL'
echo '$env:ERLANGEXE'
$webclient=New-Object System.Net.WebClient
$webclient.DownloadFile('$env:ERLANGURL', '$env:ERLANGEXE')
$webclient.DownloadFile('$env:RMQURL', '$env:RMQEXE')