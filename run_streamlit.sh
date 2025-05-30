#!/bin/bash

# 환경 변수 설정
export API_HOST=localhost
export API_PORT=8000

# Nginx 설정 복사 및 재시작
sudo cp nginx.conf /etc/nginx/sites-available/chimchak-search
sudo ln -sf /etc/nginx/sites-available/chimchak-search /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# Streamlit 실행
streamlit run app.py --server.address 127.0.0.1 --server.port 8080