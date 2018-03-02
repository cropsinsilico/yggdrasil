echo $env:ERLANGURL
echo $env:RMQURL
$webclient=New-Object System.Net.WebClient
$webclient.DownloadFile('$env:ERLANGURL', '$env:ERLANGEXE')
$webclient.DownloadFile('$env:RMQURL', '$env:RMQEXE')