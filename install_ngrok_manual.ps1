# Скрипт установки ngrok через PowerShell
Write-Host "📦 Установка ngrok для Windows..." -ForegroundColor Green

# Проверяем установлен ли Node.js
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js найден: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js не установлен!" -ForegroundColor Red
    Write-Host "💡 Скачай с https://nodejs.org/" -ForegroundColor Yellow
    Write-Host "   Выбирай LTS версию" -ForegroundColor Yellow
    Read-Host "Нажми Enter для выхода..."
    exit
}

# Устанавливаем ngrok
Write-Host "📦 Установка ngrok..." -ForegroundColor Yellow
try {
    npm install -g ngrok
    Write-Host "✅ ngrok успешно установлен!" -ForegroundColor Green
} catch {
    Write-Host "❌ Ошибка установки ngrok" -ForegroundColor Red
    Write-Host $Error[0].Exception.Message -ForegroundColor Red
}

Write-Host "🎉 Готово! Теперь можешь запустить:" -ForegroundColor Green
Write-Host "python public_server.py" -ForegroundColor Cyan

Read-Host "Нажми Enter для выхода..."
