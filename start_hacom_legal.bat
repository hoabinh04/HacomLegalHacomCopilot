@echo off
chcp 65001 > nul
title HACOM Legal Copilot - Server Launcher
echo =================================================================
echo   TẬP ĐOÀN HACOM HOLDINGS - LEGAL COPILOT SYSTEM
echo =================================================================
echo [+] Đang thiết lập biến môi trường...
set HACOM_LLM_URL=http://localhost:50050
set HACOM_LEGAL_MODEL=qwen3:8b
set HACOM_LLM_TIMEOUT=120

echo [+] Đang khởi động Server...
C:\KHMT\HacomHolding\HacomKTKT\.conda-env\python.exe app.py
pause
