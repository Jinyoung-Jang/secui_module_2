# System Metrics Collector

Python 기반 시스템 리소스 메트릭 수집 에이전트입니다. CPU, 메모리, 디스크, 네트워크 메트릭을 실시간으로 수집하여 API 서버로 전송합니다.

## 기능

- **CPU 메트릭**: 전체/코어별 사용률, 로드 평균
- **메모리 메트릭**: 메모리 및 스왑 사용량
- **디스크 메트릭**: 디스크 사용량, I/O 통계, Inode 정보
- **네트워크 메트릭**: 네트워크 I/O, 패킷 전송률, 연결 통계
- **로컬 버퍼링**: 네트워크 장애 시 메트릭을 로컬에 저장하여 나중에 재전송
- **유연한 설정**: YAML 기반 설정으로 메트릭 종류 및 수집 주기 제어

## 요구사항

- Python 3.9 이상
- 운영체제: Linux, Windows, macOS

## 설치

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 개발 환경 설정 (테스트 실행 시):
```bash
pip install -r requirements-dev.txt
```

## 설정

`config/collector-config.yaml` 파일을 편집하여 수집기를 설정합니다:

```yaml
collector:
  interval: 5                          # 수집 간격 (초)
  server_url: http://localhost:8000    # API 서버 URL
  api_key: ${API_KEY}                  # API 인증 키 (환경변수)
  hostname: ""                         # 호스트명 (자동 감지)

metrics:
  cpu:
    enabled: true
    per_cpu: true
  memory:
    enabled: true
  disk:
    enabled: true
    interval: 30
  network:
    enabled: true
```

### 환경변수

API 키는 환경변수로 설정하는 것을 권장합니다:

```bash
export API_KEY=your_api_key_here
```

또는 `.env` 파일을 사용:
```
API_KEY=your_api_key_here
```

## 실행

### 기본 실행

```bash
python src/main.py
```

### 커스텀 설정 파일 사용

```bash
python src/main.py -c /path/to/config.yaml
```

### 백그라운드 실행 (Linux/macOS)

```bash
nohup python src/main.py > collector.log 2>&1 &
```

### systemd 서비스로 실행 (Linux)

`/etc/systemd/system/metrics-collector.service` 파일 생성:

```ini
[Unit]
Description=System Metrics Collector
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/collector
Environment="API_KEY=your_api_key"
ExecStart=/usr/bin/python3 /path/to/collector/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

서비스 시작:
```bash
sudo systemctl daemon-reload
sudo systemctl enable metrics-collector
sudo systemctl start metrics-collector
sudo systemctl status metrics-collector
```

## 테스트

단위 테스트 실행:

```bash
cd tests
pytest test_metrics_collector.py -v
```

커버리지 포함:

```bash
pytest test_metrics_collector.py -v --cov=../src --cov-report=html
```

## 로그

로그는 설정 파일의 `logging` 섹션에서 제어할 수 있습니다:

- 콘솔 출력 (기본값)
- 파일 로그 (경로 지정 시)
- 로그 레벨: DEBUG, INFO, WARNING, ERROR, CRITICAL

로그 파일 확인:
```bash
tail -f collector.log
```

## 버퍼링

네트워크 장애로 API 서버에 연결할 수 없는 경우, 메트릭은 로컬 버퍼 디렉토리에 저장됩니다:

- 기본 위치: `./buffer`
- 최대 크기: 100MB (설정 가능)
- 연결 복구 시 자동으로 재전송

버퍼 통계는 종료 시 로그에 기록됩니다.

## 성능

- CPU 오버헤드: < 5%
- 메모리 사용량: < 100MB
- 수집 지연: < 1초

## 문제 해결

### Permission Denied 오류

일부 메트릭(네트워크 연결 등)은 관리자 권한이 필요할 수 있습니다:

```bash
sudo python src/main.py
```

### 모듈을 찾을 수 없음

PYTHONPATH를 설정:

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/collector/src"
```

### API 서버 연결 실패

- API 서버 URL이 올바른지 확인
- 네트워크 연결 확인
- API 키가 올바른지 확인
- 방화벽 설정 확인

## 라이선스

MIT License
