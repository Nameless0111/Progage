@echo off
echo 🌍 Запуск ngrok...
ngrok http 8000 --log=stdout
echo ✅ ngrok запущен!
echo 🌐 Панель ngrok: http://localhost:4040
echo 🛑 Остановка: Ctrl+C
pause
