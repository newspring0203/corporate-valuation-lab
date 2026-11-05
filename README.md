# Corporate Valuation Lab

**가상의 제조기업 A사를 DCF·시장배수·순자산가치로 평가하고, Excel과 Python의 계산 결과를 비교한 프로젝트입니다.**

[벨로그 학습 기록](https://velog.io/@bomi0203/posts)

## 구현 내용

- 5개년 FCFF 추정, 잔존가치 및 지분가치 계산
- 비교기업 EV/EBITDA·PER와 조정 순자산가치 계산
- WACC·영구성장률 민감도, 사업 시나리오와 실사 조정 예시
- 입력 검증, Excel 저장값 대사와 자동 테스트

## 실행

Python 3.9 이상. 표준 라이브러리만 사용합니다.

```bash
python3 -m valuation_lab --output local/results.json
python3 -m unittest discover -s tests -v
```

## 주요 결과

가상의 기준일은 2025-12-31이며, 금액 단위는 억 원입니다.

| 평가방법 | 지분가치 |
|---|---:|
| DCF | 66.44 |
| EV/EBITDA | 76.00 |
| PER | 75.00 |
| 조정 순자산가치 | 70.00 |

DCF는 성장률 8·6·5·4·3%, EBIT 마진 12%, WACC 12%, 영구성장률 2%, 순차입금 20을 가정했습니다. 전체 입력과 추가 조정은 `valuation_lab/example.py`와 `DCFInputs`에서 확인할 수 있습니다.

## 파일 구성

| 경로 | 내용 |
|---|---|
| `valuation_lab/models.py` | WACC·DCF·Comps·NAV 계산 및 입력 검증 |
| `valuation_lab/example.py` | A사·비교기업 가정, 민감도·시나리오·실사 조정 |
| `valuation_lab/__main__.py` | 예시 실행 및 JSON 저장 |
| `tests/` | 계산·예외조건·Excel 저장값 대사 테스트 |
| `excel/A_company_valuation.xlsx` | DCF·Comps·NAV Excel 모델 |

## 검증

로컬에서 **24개 테스트 통과**를 확인했습니다. WACC와 영구성장률의 관계, 운전자본 증가액, 잔존가치, 금액 배율, PER·NAV의 계산 범위 등을 점검했습니다.

Excel 테스트는 저장된 수식·계산값과 Python 결과를 대사합니다. Excel 파일이 없으면 해당 테스트 1개를 건너뜁니다.

## 적용 범위

기업과 비교기업, 사업계획은 모두 가상의 사례입니다. 매출 비율로 투자·감가상각을 추정하고 세금을 단순화했습니다. 계산의 검증과 가정의 타당성 검토는 구분합니다.
