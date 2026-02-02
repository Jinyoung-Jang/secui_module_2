# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드 문서입니다.

## 프로젝트 개요

시스템 리소스 메트릭 모니터링 시스템 - CPU, 메모리, 디스크, 네트워크 메트릭을 실시간으로 수집, 저장, 시각화하고 알림을 제공하는 서버 모니터링 시스템입니다.

## 시스템 아키텍처

분산 아키텍처를 따르며 3개의 주요 컴포넌트로 구성됩니다:

1. **Collector (수집기)**: 모니터링 대상 서버에 배포되는 Python 기반 에이전트
   - `psutil` 라이브러리를 사용하여 시스템 메트릭 수집
   - 대부분의 메트릭은 5초 간격으로 수집
   - HTTPS를 통해 API 서버로 데이터 전송
   - 네트워크 장애 대비 로컬 버퍼링 지원

2. **API Server (API 서버)**: FastAPI 기반 백엔드 서버
   - 수집기로부터 메트릭 수신 (`POST /api/v1/metrics/collect`)
   - 시계열 데이터베이스(InfluxDB/Prometheus)에 데이터 저장
   - 대시보드용 쿼리 엔드포인트 제공
   - 알림 규칙 관리 및 알림 트리거

3. **Alert Manager (알림 관리자)**: 자율적인 알림 시스템
   - 임계값 기반 규칙에 따라 메트릭 평가
   - 알림 폭주 방지 (5분간 중복 제거)
   - 다중 채널 지원 (Slack, Email, Webhook)

4. **Dashboard (대시보드)**: 시각화를 위한 웹 UI
   - 10초 자동 새로고침으로 실시간 메트릭 표시
   - 다양한 대시보드 뷰 (개요, CPU, 메모리, 디스크, 네트워크)
   - 시간 범위 선택 (1시간, 6시간, 24시간, 7일, 30일)

## 디렉토리 구조

```
module-3/
├── collector/           # 메트릭 수집 에이전트
│   ├── src/            # 메인 수집기 코드
│   ├── config/         # 설정 템플릿
│   └── tests/          # 단위 테스트
├── api-server/         # 백엔드 API 서비스
│   ├── src/
│   │   ├── routes/     # API 엔드포인트
│   │   ├── models/     # 데이터 모델
│   │   ├── services/   # 비즈니스 로직
│   │   └── middleware/ # 인증, 로깅 등
│   ├── config/         # 서버 설정
│   └── tests/          # API 테스트
├── alert-manager/      # 알림 처리 엔진
│   ├── src/            # 알림 평가 로직
│   └── tests/          # 알림 테스트
├── dashboard/          # 웹 프론트엔드
│   ├── src/            # React/Vue 컴포넌트
│   └── public/         # 정적 자산
├── database/           # 데이터베이스 스키마 및 마이그레이션
│   ├── migrations/     # 스키마 버전 관리
│   └── schemas/        # InfluxDB/PostgreSQL 스키마
├── scripts/            # 배포 및 유틸리티 스크립트
├── tests/integration/  # E2E 테스트
└── docs/               # 문서
```

## 메트릭 수집 주기

- **CPU/메모리/네트워크**: 5초
- **디스크 사용량**: 30초
- **정적 정보** (코어 수, 전체 메모리): 시작 시 1회

## 데이터 보관 정책

| 해상도 | 보관 기간 | 설명 |
|-------|---------|------|
| 5초 | 24시간 | 원본 데이터 |
| 1분 | 7일 | 평균값 (12개 포인트) |
| 5분 | 30일 | 평균값 (60개 포인트) |

## 주요 메트릭

### CPU 메트릭
- `cpu.usage.total`: 전체 CPU 사용률 (%)
- `cpu.usage.user`, `cpu.usage.system`, `cpu.usage.idle`, `cpu.usage.iowait`
- `cpu.cores.usage`: 코어별 사용률
- `cpu.load.average.1m/5m/15m`: 로드 평균

### 메모리 메트릭
- `memory.total`, `memory.used`, `memory.available`, `memory.free`
- `memory.usage.percent`: 메모리 사용률 (%)
- `memory.buffers`, `memory.cached`
- `swap.total`, `swap.used`, `swap.usage.percent`

### 디스크 메트릭
- `disk.usage.total/used/free/percent`: 디스크 공간
- `disk.io.read.bytes/write.bytes`: I/O 처리량 (bytes/sec)
- `disk.io.read.count/write.count`: IOPS
- `disk.inode.total/used/usage.percent`: Inode 사용률

### 네트워크 메트릭
- `network.io.bytes.sent/recv`: 네트워크 처리량 (bytes/sec)
- `network.io.packets.sent/recv`: 패킷 전송률
- `network.io.errors.in/out`, `network.io.dropped.in/out`
- `network.connections.tcp/udp/established/time_wait`

## API 엔드포인트

```
GET  /api/v1/metrics/current    # 최신 메트릭 값 조회
GET  /api/v1/metrics/history    # 시계열 데이터 조회
POST /api/v1/metrics/collect    # 수집기 데이터 제출
GET  /api/v1/alerts             # 알림 이력 조회
POST /api/v1/alerts/rules       # 알림 규칙 생성
GET  /api/v1/health             # 시스템 헬스체크
```

## 기술 스택

- **Collector (수집기)**: Python 3.9+, psutil, requests, schedule
- **API Server (API 서버)**: FastAPI, Pydantic, JWT 인증
- **Database (데이터베이스)**: InfluxDB 2.x (시계열) + PostgreSQL (메타데이터)
- **Dashboard (대시보드)**: Grafana
- **Alert Manager (알림 관리자)**: 커스텀 Python (SMTP, Slack API, Webhooks)

## 설정

### 수집기 설정 (`collector/config/collector-config.yaml`)
```yaml
collector:
  interval: 5s
  server_url: https://monitoring.example.com
  api_key: ${API_KEY}

metrics:
  cpu:
    enabled: true
    per_cpu: true
  memory:
    enabled: true
  disk:
    enabled: true
    exclude_devices: [tmpfs, devtmpfs]
  network:
    enabled: true
    interfaces: [eth0, eth1]
```

## 기본 알림 규칙

| 메트릭 | 조건 | 심각도 |
|-------|-----|--------|
| CPU > 80% (5분) | WARNING | |
| CPU > 95% (2분) | CRITICAL | |
| 메모리 > 85% | WARNING | |
| 메모리 > 95% | CRITICAL | |
| 디스크 > 80% | WARNING | |
| 디스크 > 90% | CRITICAL | |
| I/O Wait > 50% (5분) | WARNING | |

## 성능 요구사항

- **수집기 오버헤드**: < 5% CPU, < 100MB 메모리
- **수집 지연**: < 1초
- **수집 성공률**: > 99.9%
- **API 쿼리 지연**: < 200ms (현재 메트릭), < 1초 (24시간 시계열)
- **대시보드 로딩 시간**: < 2초

## 개발 단계

### Phase 1 (MVP - 4주)
- 1-2주차: 수집기 개발 (CPU, 메모리 메트릭)
- 3주차: API 서버 + 데이터베이스 연동
- 4주차: 기본 대시보드 + 알림 기능

### Phase 2 (기능 확장 - 4주)
- 5-6주차: 디스크 + 네트워크 메트릭 추가
- 7주차: 고급 알림 규칙
- 8주차: 대시보드 개선

### Phase 3 (최적화 - 2주)
- 9주차: 성능 튜닝 + 테스트
- 10주차: 문서화 + 배포 자동화

## 데이터 모델

### InfluxDB 스키마
```
measurement: system_metrics
tags:
  - host: hostname
  - metric_type: cpu|memory|disk|network
  - device: device_name
fields:
  - value: float
  - unit: string
timestamp: nanosecond precision
```

### PostgreSQL 알림 테이블
- `alert_rules`: 알림 규칙 정의 (이름, 메트릭, 임계값, 심각도, 채널)
- `alert_history`: 알림 발생 및 해결 이벤트

## 보안

- 모든 통신에 HTTPS/TLS 1.2+ 사용
- JWT 또는 API Key 인증
- Rate Limiting: 수집기당 100 req/min
- 로그나 API 응답에 민감한 데이터 포함 금지

## 배포

- **수집기**: systemd 서비스 또는 Docker 컨테이너
- **서버**: Docker Compose 또는 Kubernetes
- 멀티 플랫폼 지원: Linux, Windows, macOS

## 테스트 전략

- 각 수집기 메트릭 타입별 단위 테스트
- API 엔드포인트 테스트 (pytest/FastAPI TestClient)
- 전체 데이터 흐름을 시뮬레이션하는 통합 테스트
- 100개 이상의 동시 수집기 부하 테스트
