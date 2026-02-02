# PRD: 시스템 리소스 메트릭 모니터링 시스템

## 1. 개요

### 1.1 목적
서버의 시스템 리소스를 실시간으로 수집, 저장, 시각화하여 시스템 상태를 모니터링하고 성능 이슈를 사전에 감지하는 시스템을 구축합니다.

### 1.2 배경
- 서버 리소스의 비정상적인 사용은 서비스 장애로 이어질 수 있음
- 사전 경보 시스템을 통해 문제를 조기에 발견하고 대응 필요
- 리소스 사용 패턴 분석을 통한 용량 계획 수립

### 1.3 목표
- 5초 간격으로 실시간 메트릭 수집
- 99.9% 수집 성공률 달성
- 수집 오버헤드 CPU 사용량 5% 이하 유지
- 30일간의 메트릭 데이터 보관

---

## 2. 핵심 메트릭 정의

### 2.1 CPU 메트릭

| 메트릭명 | 설명 | 단위 | 수집 주기 |
|---------|------|------|----------|
| `cpu.usage.total` | 전체 CPU 사용률 | % | 5초 |
| `cpu.usage.user` | 사용자 프로세스 CPU 사용률 | % | 5초 |
| `cpu.usage.system` | 시스템 프로세스 CPU 사용률 | % | 5초 |
| `cpu.usage.idle` | 유휴 상태 비율 | % | 5초 |
| `cpu.usage.iowait` | I/O 대기 시간 비율 | % | 5초 |
| `cpu.cores.count` | CPU 코어 수 | count | 1회 |
| `cpu.cores.usage` | 코어별 사용률 | % | 5초 |
| `cpu.load.average.1m` | 1분 평균 로드 | float | 5초 |
| `cpu.load.average.5m` | 5분 평균 로드 | float | 5초 |
| `cpu.load.average.15m` | 15분 평균 로드 | float | 5초 |

### 2.2 메모리 메트릭

| 메트릭명 | 설명 | 단위 | 수집 주기 |
|---------|------|------|----------|
| `memory.total` | 전체 메모리 용량 | bytes | 1회 |
| `memory.used` | 사용 중인 메모리 | bytes | 5초 |
| `memory.available` | 사용 가능한 메모리 | bytes | 5초 |
| `memory.free` | 완전히 빈 메모리 | bytes | 5초 |
| `memory.usage.percent` | 메모리 사용률 | % | 5초 |
| `memory.buffers` | 버퍼 메모리 | bytes | 5초 |
| `memory.cached` | 캐시 메모리 | bytes | 5초 |
| `swap.total` | 전체 스왑 용량 | bytes | 1회 |
| `swap.used` | 사용 중인 스왑 | bytes | 5초 |
| `swap.free` | 사용 가능한 스왑 | bytes | 5초 |
| `swap.usage.percent` | 스왑 사용률 | % | 5초 |

### 2.3 디스크 메트릭

| 메트릭명 | 설명 | 단위 | 수집 주기 |
|---------|------|------|----------|
| `disk.usage.total` | 디스크 전체 용량 | bytes | 30초 |
| `disk.usage.used` | 사용 중인 디스크 공간 | bytes | 30초 |
| `disk.usage.free` | 사용 가능한 디스크 공간 | bytes | 30초 |
| `disk.usage.percent` | 디스크 사용률 | % | 30초 |
| `disk.io.read.bytes` | 디스크 읽기 바이트 | bytes/sec | 5초 |
| `disk.io.write.bytes` | 디스크 쓰기 바이트 | bytes/sec | 5초 |
| `disk.io.read.count` | 디스크 읽기 작업 수 | ops/sec | 5초 |
| `disk.io.write.count` | 디스크 쓰기 작업 수 | ops/sec | 5초 |
| `disk.io.read.time` | 읽기 작업 시간 | ms | 5초 |
| `disk.io.write.time` | 쓰기 작업 시간 | ms | 5초 |
| `disk.inode.total` | 전체 inode 수 | count | 30초 |
| `disk.inode.used` | 사용 중인 inode 수 | count | 30초 |
| `disk.inode.usage.percent` | inode 사용률 | % | 30초 |

### 2.4 네트워크 메트릭

| 메트릭명 | 설명 | 단위 | 수집 주기 |
|---------|------|------|----------|
| `network.io.bytes.sent` | 송신 바이트 | bytes/sec | 5초 |
| `network.io.bytes.recv` | 수신 바이트 | bytes/sec | 5초 |
| `network.io.packets.sent` | 송신 패킷 수 | packets/sec | 5초 |
| `network.io.packets.recv` | 수신 패킷 수 | packets/sec | 5초 |
| `network.io.errors.in` | 수신 에러 | count/sec | 5초 |
| `network.io.errors.out` | 송신 에러 | count/sec | 5초 |
| `network.io.dropped.in` | 수신 드롭 패킷 | count/sec | 5초 |
| `network.io.dropped.out` | 송신 드롭 패킷 | count/sec | 5초 |
| `network.connections.tcp` | TCP 연결 수 | count | 5초 |
| `network.connections.udp` | UDP 연결 수 | count | 5초 |
| `network.connections.established` | ESTABLISHED 상태 연결 | count | 5초 |
| `network.connections.time_wait` | TIME_WAIT 상태 연결 | count | 5초 |

---

## 3. 기능 요구사항

### 3.1 메트릭 수집 (Collector)

#### 필수 기능
- [ ] 시스템 리소스 메트릭을 주기적으로 수집
- [ ] 멀티 플랫폼 지원 (Linux, Windows, macOS)
- [ ] 수집 실패 시 자동 재시도 (최대 3회)
- [ ] 수집기 상태 헬스체크 제공
- [ ] 설정 파일을 통한 수집 주기 조정

#### 선택 기능
- [ ] 특정 메트릭 선택적 수집
- [ ] 커스텀 메트릭 플러그인 시스템
- [ ] 수집 데이터 로컬 버퍼링 (네트워크 장애 대비)

### 3.2 데이터 저장 (Storage)

#### 필수 기능
- [ ] 시계열 데이터베이스에 메트릭 저장
- [ ] 데이터 압축 및 다운샘플링
- [ ] 자동 데이터 보관 정책 (30일)
- [ ] 고가용성 구성 지원

#### 데이터 보관 정책
| 해상도 | 보관 기간 | 설명 |
|-------|---------|------|
| 5초 | 24시간 | 원본 데이터 |
| 1분 | 7일 | 12개 포인트 평균 |
| 5분 | 30일 | 60개 포인트 평균 |

### 3.3 알림 (Alerting)

#### 필수 기능
- [ ] 임계값 기반 알림 규칙 설정
- [ ] 알림 채널 지원 (Slack, Email, Webhook)
- [ ] 알림 중복 방지 (동일 알림 5분간 1회만 발송)
- [ ] 알림 이력 저장

#### 기본 알림 규칙
| 메트릭 | 조건 | 심각도 |
|-------|------|--------|
| CPU 사용률 | > 80% (5분 지속) | WARNING |
| CPU 사용률 | > 95% (2분 지속) | CRITICAL |
| 메모리 사용률 | > 85% | WARNING |
| 메모리 사용률 | > 95% | CRITICAL |
| 디스크 사용률 | > 80% | WARNING |
| 디스크 사용률 | > 90% | CRITICAL |
| 디스크 I/O Wait | > 50% (5분 지속) | WARNING |

### 3.4 시각화 (Visualization)

#### 필수 기능
- [ ] 실시간 메트릭 대시보드
- [ ] 시계열 그래프 (라인 차트)
- [ ] 현재 값 게이지 표시
- [ ] 시간 범위 선택 (1시간, 6시간, 24시간, 7일, 30일)
- [ ] 자동 새로고침 (10초 간격)

#### 대시보드 구성
1. **시스템 개요 대시보드**
   - CPU, 메모리, 디스크, 네트워크 주요 지표 한눈에 표시

2. **CPU 상세 대시보드**
   - 전체 CPU 사용률 추이
   - 코어별 사용률
   - Load Average

3. **메모리 상세 대시보드**
   - 메모리 사용률 추이
   - 메모리 구성 (used/buffers/cached/free)
   - 스왑 사용률

4. **디스크 상세 대시보드**
   - 디스크 사용률 (파티션별)
   - 디스크 I/O 추이
   - inode 사용률

5. **네트워크 상세 대시보드**
   - 네트워크 트래픽 (in/out)
   - 패킷 에러/드롭률
   - 연결 상태별 통계

### 3.5 API

#### 필수 엔드포인트
```
GET  /api/v1/metrics/current              # 현재 메트릭 조회
GET  /api/v1/metrics/history              # 시계열 메트릭 조회
POST /api/v1/metrics/collect              # 메트릭 수집 (수집기 → 서버)
GET  /api/v1/alerts                       # 알림 목록 조회
POST /api/v1/alerts/rules                 # 알림 규칙 생성
GET  /api/v1/health                       # 시스템 헬스체크
```

---

## 4. 기술 스펙

### 4.1 시스템 아키텍처

```
┌─────────────────┐
│  Monitored      │
│  Server(s)      │
│                 │
│  ┌───────────┐  │
│  │ Collector │  │ (Agent)
│  │  Process  │  │
│  └─────┬─────┘  │
└────────┼────────┘
         │ HTTPS
         ▼
┌─────────────────────────────────────┐
│     Monitoring Server               │
│                                     │
│  ┌──────────┐    ┌──────────────┐  │
│  │   API    │───▶│  Time Series │  │
│  │  Server  │    │   Database   │  │
│  └────┬─────┘    └──────────────┘  │
│       │                             │
│       │          ┌──────────────┐  │
│       └─────────▶│  Alert       │  │
│                  │  Manager     │  │
│                  └──────────────┘  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Dashboard     │
│   (Web UI)      │
└─────────────────┘
```

### 4.2 기술 스택

#### Collector (Agent)
- **언어**: Python 3.9+
- **핵심 라이브러리**:
  - `psutil`: 시스템 메트릭 수집
  - `requests`: HTTP 통신
  - `schedule`: 주기적 작업 실행
  - `logging`: 로깅

#### API Server
- **프레임워크**: FastAPI (Python) 또는 Express.js (Node.js)
- **인증**: JWT 기반 인증
- **문서화**: OpenAPI/Swagger

#### Database
- **시계열 DB**: InfluxDB 2.x 또는 Prometheus + TimescaleDB
- **메타데이터 저장**: PostgreSQL 또는 SQLite

#### Visualization
- **대시보드**: Grafana 또는 커스텀 React 대시보드
- **차트 라이브러리**: Chart.js, Apache ECharts, D3.js

#### Alert Manager
- **알림 엔진**: 자체 구현 또는 Prometheus AlertManager
- **알림 채널**:
  - Slack Incoming Webhooks
  - SMTP (Email)
  - Generic Webhooks

### 4.3 데이터 모델

#### InfluxDB 스키마 예시
```
measurement: system_metrics
tags:
  - host: hostname
  - metric_type: cpu|memory|disk|network
  - device: (디스크명, 네트워크 인터페이스명 등)
fields:
  - value: float
  - unit: string
timestamp: nanosecond precision
```

#### PostgreSQL 알림 테이블
```sql
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    condition VARCHAR(50) NOT NULL, -- >, <, >=, <=, ==
    threshold FLOAT NOT NULL,
    duration_seconds INT,
    severity VARCHAR(50) NOT NULL, -- INFO, WARNING, CRITICAL
    channels JSONB, -- ["slack", "email"]
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE alert_history (
    id SERIAL PRIMARY KEY,
    rule_id INT REFERENCES alert_rules(id),
    triggered_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    metric_value FLOAT,
    message TEXT,
    status VARCHAR(50) -- FIRING, RESOLVED
);
```

---

## 5. 성능 요구사항

### 5.1 수집 성능
- CPU 오버헤드: < 5%
- 메모리 사용량: < 100MB per collector
- 수집 지연: < 1초
- 수집 성공률: > 99.9%

### 5.2 저장 성능
- 쓰기 처리량: > 10,000 points/sec
- 쓰기 지연: < 500ms (p95)
- 저장 공간: ~100MB per host per day (raw data)

### 5.3 조회 성능
- 실시간 메트릭 조회: < 200ms
- 시계열 데이터 조회 (24시간): < 1초
- 대시보드 로딩: < 2초

### 5.4 확장성
- 수평 확장 가능 (여러 서버 모니터링)
- 최소 100개 호스트 동시 모니터링 지원
- 컬렉터와 서버 간 비동기 통신

---

## 6. 보안 요구사항

### 6.1 통신 보안
- [ ] HTTPS 통신 (TLS 1.2+)
- [ ] API 인증 (JWT 또는 API Key)
- [ ] Rate Limiting (100 req/min per collector)

### 6.2 데이터 보안
- [ ] 민감 정보 마스킹 (API 응답)
- [ ] 접근 권한 관리 (RBAC)
- [ ] 감사 로그 기록

### 6.3 인프라 보안
- [ ] 방화벽 규칙 설정
- [ ] 최소 권한 원칙 적용
- [ ] 정기적 보안 패치

---

## 7. 배포 및 운영

### 7.1 배포 방식
- **Collector**:
  - 바이너리 배포 또는 Python 패키지
  - systemd 서비스 등록
  - Docker 컨테이너 지원

- **Server**:
  - Docker Compose 배포
  - Kubernetes 배포 (선택)

### 7.2 설정 관리
```yaml
# collector-config.yaml 예시
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

logging:
  level: INFO
  file: /var/log/collector.log
```

### 7.3 모니터링 및 로깅
- Collector 자체 상태 메트릭 수집
- 구조화된 로그 형식 (JSON)
- 로그 레벨: DEBUG, INFO, WARNING, ERROR, CRITICAL

---

## 8. 개발 일정

### Phase 1: MVP (4주)
- Week 1-2: Collector 개발 (CPU, Memory 메트릭)
- Week 3: API Server 및 데이터베이스 연동
- Week 4: 기본 대시보드 및 알림 기능

### Phase 2: 기능 확장 (4주)
- Week 5-6: 디스크 및 네트워크 메트릭 추가
- Week 7: 알림 규칙 고도화
- Week 8: 대시보드 고도화 및 UX 개선

### Phase 3: 최적화 및 안정화 (2주)
- Week 9: 성능 최적화 및 테스트
- Week 10: 문서화 및 배포 자동화

---

## 9. 성공 지표 (KPI)

### 9.1 시스템 안정성
- 수집기 가동률: > 99.9%
- API 가용성: > 99.95%
- 데이터 손실률: < 0.01%

### 9.2 성능 지표
- 평균 수집 지연: < 500ms
- 대시보드 로딩 시간: < 2초
- 알림 발송 지연: < 30초

### 9.3 운영 효율성
- 장애 사전 감지율: > 80%
- 오탐률: < 5%
- 평균 문제 해결 시간(MTTR) 감소: > 30%

---

## 10. 리스크 및 대응 방안

| 리스크 | 가능성 | 영향도 | 대응 방안 |
|-------|-------|-------|----------|
| 수집 오버헤드로 인한 서버 성능 저하 | 중 | 높음 | 수집 주기 조정, 경량화된 라이브러리 사용 |
| 대량 데이터로 인한 저장소 용량 초과 | 높음 | 중 | 다운샘플링, 자동 삭제 정책 |
| 네트워크 장애로 인한 데이터 유실 | 중 | 중 | 로컬 버퍼링, 재전송 메커니즘 |
| 알림 폭주 (Alert Storm) | 중 | 중 | 알림 그룹화, Rate Limiting |
| 멀티 플랫폼 호환성 이슈 | 낮음 | 중 | psutil 라이브러리 활용, 플랫폼별 테스트 |

---

## 11. 참고 자료

### 11.1 유사 제품
- Prometheus + Node Exporter
- Datadog Agent
- New Relic Infrastructure
- Netdata
- Telegraf (InfluxData)

### 11.2 기술 문서
- [psutil Documentation](https://psutil.readthedocs.io/)
- [InfluxDB Documentation](https://docs.influxdata.com/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

## 12. 부록

### 12.1 용어 정의
- **메트릭(Metric)**: 측정 가능한 시스템 지표
- **수집기(Collector/Agent)**: 메트릭을 수집하는 에이전트 프로그램
- **시계열 데이터(Time Series Data)**: 시간 순서대로 기록된 데이터
- **다운샘플링(Downsampling)**: 데이터 해상도를 낮춰 저장 공간 절약
- **IOPS**: Input/Output Operations Per Second

### 12.2 FAQ
**Q: 수집기 설치 시 root 권한이 필요한가요?**
A: 일부 시스템 메트릭 수집을 위해 권한이 필요할 수 있으나, 대부분의 메트릭은 일반 사용자 권한으로 수집 가능합니다.

**Q: 기존 모니터링 시스템과 병행 사용이 가능한가요?**
A: 예, 수집기의 오버헤드가 낮아 다른 모니터링 도구와 함께 사용 가능합니다.

**Q: 클라우드 환경(AWS, GCP 등)에서도 사용 가능한가요?**
A: 예, 클라우드 VM 인스턴스에 수집기를 설치하여 사용 가능합니다.

---

**문서 버전**: 1.0
**작성일**: 2026-02-02
**작성자**: Development Team
**승인자**: [TBD]
