@echo off
chcp 65001 >nul
cd /d "C:\Users\Owner\Downloads\Psytint 260215\Уламжлалт онооны загвар\loan_dashboard"
echo [%date% %time%] Running ETL...
py etl_cowork.py
echo [%date% %time%] Building report...
py report_cowork.py
echo [%date% %time%] Done.
