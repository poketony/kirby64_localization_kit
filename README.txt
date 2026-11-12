최신 빌드 — 2026-11-12 v4
게임 실행 후 수정한 최신 RGBA 6개 재반영. 전체 PNG 350개와 두 글자 모델 포함.
ROM: build/kirby64-ko-graphics-20261112-v4.z64
검사: codex-lab/knowledge/rgba-refresh-29.md
재추출 350/350·체크섬·변경 범위·모델 보존 검사 통과. 이번 버전 게임 실행은 미실시.
이하 이전 시점 기록입니다.

최신 빌드 — 2026-11-12 v3
사용자 제공 형편없네요·축하합니다! 모델 두 개 및 PNG 350개 반영.
ROM: build/kirby64-ko-graphics-20261112-v3.z64
검사: codex-lab/knowledge/success-image-28.md
모델 재추출·체크섬·변경 범위 통과. 실제 게임 애니메이션은 미검증.
이하 이전 시점 기록입니다.

최신 빌드 — 2026-11-12 v2
형편없네요: 사용자 제공 PNG 기반 모델 반영 완료.
ROM: build/kirby64-ko-graphics-20261112-v2.z64
검사 기록: codex-lab/knowledge/failure-image-27.md
기존 PNG 350개 유지. 모델 재추출·체크섬·변경 범위 검사 통과.
축하합니다 모델은 미반영. 실제 게임 애니메이션은 미검증.
이하 이전 시점 기록입니다.

최신 빌드 — 2026-11-12
workspace/editable_rgba의 PNG 350개를 반영했습니다.
ROM: build/kirby64-ko-graphics-20261112.z64
검사 기록: codex-lab/knowledge/rom-build-26.md
PNG 누락 0. 재추출 350/350 일치, 체크섬·변경 범위·헤더·패딩 검사 통과.
글자 모델 2개는 재작업 상태로 미반영. 에뮬레이터 부팅·플레이 검사는 미실시.
아래 내용에는 이전 작업 시점의 설명이 포함되어 있습니다.

별의 커비 64 일본어판 Rev3 — 한글화 작업 키트

최신 상태: 보관 PNG 321개 중 9개는 사용자 반려로 재작업 필요입니다.
カイショウナシ는 지오메트리 0x30005로 위치를 확정했습니다. 한국어 메시와 ROM 반영은 미작업입니다.
분석: codex-lab/knowledge/boss-failure-12.md
작업 목록: codex-lab/knowledge/graphics-worklist.md

이번에 준비한 범위
번역 대상 그래픽 목록, 이미지/글리프/내부 ASCII 문자열 추출, 고정 크기 재삽입,
한글 문구의 비트맵 생성, N64 체크섬 갱신, 수정 롬 재추출·변경 범위 검증입니다.
현재 workspace/edits의 그래픽은 총 321개입니다. 영어 원본 그래픽은 번역하지 않으며 b0_0027은 원본으로 복구했습니다. 스태프롤은 영어로 통일했습니다.
2026-11-11 피드백 11차: 타이틀 색·폰트·잔여 글자·채색·정렬 25개를 수정했습니다.
현재 PNG 321개 중 피드백 10/11차의 57개는 ROM 반영 대기입니다. 명시적 빌드 지시 전까지 ROM을 수정하지 않습니다.
최신 수정: codex-lab/knowledge/feedback-11.md
수정 전후: codex-lab/knowledge/feedback-11-review.html
수정/미작업 목록: codex-lab/knowledge/graphics-worklist.md
전체 993개 리소스 목록: codex-lab/knowledge/graphics-worklist.html
화면 예제: codex-lab/knowledge/feedback-11-screen-simulation.html
기존 ROM(이전 이미지 상태): build/kirby64-ko-graphics-20261111-v2.z64
이번 PNG의 실제 게임 표시는 아직 확인하지 않았습니다.

중요한 조사 결과
메뉴의 일본어는 대부분 글리프 코드로 조립되는 문자열이 아니라 완성된 이미지입니다.
스타트·파일·옵션·미니게임 설명·월드명·적 이름·조작법·크레딧을 실제 PNG로 확인했습니다.
따라서 이 문구들은 translations.json → 한글 비트맵 → 원래 이미지 형식으로 처리합니다.
장식된 컬러 제목이나 복잡한 배치는 PNG를 직접 편집하는 방식이 적합합니다.

확인한 공통 크래시 폰트는 7비트 문자를 처리하며 한글/유니코드 렌더러가 아닙니다.
6×6 HUD 영숫자 이미지도 있으나 일본어 메뉴 전체를 조립하는 공통 가나 폰트로
확인된 것은 아닙니다. 이 키트에 새 런타임 한글 폰트 엔진은 포함하지 않았습니다.
발견되지 않은 독자 인코딩이나 다른 텍스트 경로가 없다고 단정하지 않습니다.

목록과 파일
  번역대상목록.csv             337개 번역 대상, 2개 추가 검토, 294개 선택 사항,
                               영어 원본 유지 1개, 완료한 타이틀 1개. 인명과 캐릭터 이름도 대상에 포함합니다.
  workspace/catalog.html       993개 이미지의 검색 가능한 썸네일 목록
  workspace/originals/         원본 PNG 993개
  workspace/translations.json  문구별 번역 입력란 (원문 미전사 항목은 설명/PNG 참고)
  workspace/edits/             수정 PNG를 넣는 곳. b0_0025.png는 기존 한글 타이틀입니다.
  workspace/fonts/             크래시 폰트·HUD 글리프 아틀라스와 글리프 맵
  workspace/native_strings.json 소스와 롬이 일치한 내부 ASCII 문자열 312개
  data/image_blocks.json       8개 뱅크의 이미지 블록 4,521개 전체 경계 목록
  verification.json            수행한 자동 검증 결과
  codex-lab/knowledge/         사람이 읽는 조사·검증 기록과 재현 방법

번역 범주 / 주요 리소스 ID
  타이틀·시스템: b0_0025~0027 (0025 완료, 0027 영문 지역 오류)
  파일·메뉴·옵션: b3_0002~0067 중 목록에 지정한 항목
  미니게임: b3_0070~0150, b3_0825~0903 중 문구·결과·승자·조작 안내
  사운드 테스트: b3_0151,0153,0154
  무비 제목: b3_0187,0189~0207,0211
  설정·보스 러시·콜렉션: b3_0212~0244 중 목록에 지정한 항목
  적·보스 이름: b3_0264~0344 (81개)
  월드명·레벨: b3_0502~0509
  일시 정지·최고 기록: b3_0751,0752
  크레딧: b4_0185~0258 (74개), b4_0259 삽화 글자 추가 검토
  HUD 테마·능력 한자: b5_0004,0167,0168,0251~0260
  조작 설명·계속/다시/포기·처음 안내: b5_0271~0311 중 목록에 지정한 항목
범위 안의 모든 이미지가 문구인 것은 아닙니다. 정확한 ID는 CSV/썸네일 목록을 보세요.

실행 환경
Python 3.10 이상. 검증 환경은 Python 3.12, Pillow 12.0.0, NumPy입니다.
키트 폴더에서 PowerShell을 열어 실행하세요.

  python -m pip install -r requirements.txt

원본 입력
모든 명령의 --rom에는 처음 제공한 무수정 일본어판 Rev3 롬을 넣습니다.
SHA-1: 03257c820b7705400c32bde1bcc3161c55814605
완성 롬은 별도 경로로 출력하고 기존 파일은 덮어쓰지 않습니다.

1. 그래픽 편집
workspace/originals에서 필요한 PNG를 복사하여 workspace/edits에 같은 이름으로 넣고
편집하세요. 예: b3_0035.png. 파일명은 리소스 ID이며 크기는 원본과 같아야 합니다.
인덱스 PNG는 팔레트와 인덱스를 그대로 유지하는 것이 가장 정확합니다.
CI4는 보통 16색, CI8은 최대 256색이며 실제 팔레트가 더 짧을 수도 있습니다.
기본 빌드는 색상 수가 넘으면 중단합니다. --quantize를 추가하면 색상 축소를 허용합니다.
CI4 중 여러 팔레트 뱅크를 가진 자산은 PNG에 첫 팔레트를 표시하며, 나머지는 보존합니다.
그러한 자산은 다른 선택 상태에서의 색도 에뮬레이터로 확인해야 합니다.
I4/I8은 L 그레이스케일, IA는 LA, RGBA16은 RGBA PNG로 내보냅니다.
I 텍스처는 게임에서 색을 입힐 수 있으므로 검은 배경의 흰 문구로 보이는 것이 정상입니다.

2. 간단한 한글 문구를 이미지로 만들기
workspace/translations.json에서 원하는 항목의 translation을 채우세요.
font_size 0은 자동 맞춤이고, 직접 지정하면 넘칠 경우 실패합니다. 줄바꿈은 \n입니다.
현재 자동 렌더링은 I/IA 단색 문구용입니다. CI/RGBA 제목·버튼은 직접 그린 PNG를 쓰세요.
여러 선택지가 한 장에 합쳐진 자산은 각 선택지의 위치를 보존하도록 수동 편집을 권합니다.

  python k64_localize.py render-text --jobs workspace\translations.json --font "C:\Windows\Fonts\malgunbd.ttf" --edits workspace\edits

글꼴 파일은 배포하지 않습니다. 본인 환경의 한글 지원 TTF/OTF 경로를 지정하세요.
생성된 문구의 크기와 가독성, 줄바꿈, 하이라이트 위치는 반드시 확인하세요.
codex-lab/knowledge/baseline.md에 b3_0035를 '옵션'으로 그리는 최소 예제가 있습니다.

3. 폰트 글리프 편집
  fonts/crash.atlas.png: 90×21, 6×7 셀 45개, 1비트 흑백 폰트.
  fonts/hud_small.atlas.png: 96×60, 6×6 셀 153개, RGBA16.
위 경로는 workspace 아래입니다. 수정본을 workspace/edits/fonts/에 넣으세요.
글리프별 문자와 셀 위치는 workspace/fonts/glyph_map.json을 참고하세요.
HUD 아틀라스와 개별 b5_0008~0160 PNG를 동시에 수정하면 충돌로 중단합니다.
글리프 슬롯 교체는 문자 인코딩의 유니코드 지원 추가와 다릅니다.
일반 메뉴의 일본어는 이 아틀라스를 바꾸어도 번역되지 않습니다.

4. 내부 문자열 편집
workspace/native_strings.json의 replacement를 채운 뒤 빌드에 --strings를 추가합니다.
진단 메시지와 개발용 스테이지 식별자 등이며 플레이용 일본어 대사 테이블은 아닙니다.
ASCII만 허용하고 원래 슬롯 길이를 넘기거나 printf 인자를 바꾸면 거부합니다.
M11... 같은 개발용 레벨 식별자는 번역 대상에서 제외하며 변경을 거부합니다.
한글 메뉴 문구는 2번의 비트맵 경로로 처리하세요.

5. 빌드

  python k64_localize.py build --rom "C:\Users\JO\Desktop\Hoshi no Kirby 64 (Japan) (Rev 3).z64" --edits workspace\edits --out build\kirby64-ko.z64

내부 문자열도 수정했다면 위 명령에 다음 옵션을 붙입니다.
  --strings workspace\native_strings.json

폰트/내부 문자열 등 체크섬 계산 영역이 바뀌면 CIC-6103 체크섬을 다시 계산합니다.
이미지는 크기·형식·헤더·숨겨진 행 패딩을 유지하여 제자리 교체합니다.
이미지 확대, 리소스 재배치, 문자열 길이 확장, 코드 수정은 지원하지 않습니다.

6. 저장된 롬 검증 및 재추출

  python k64_localize.py verify --rom "C:\Users\JO\Desktop\Hoshi no Kirby 64 (Japan) (Rev 3).z64" --candidate build\kirby64-ko.z64 --report build\kirby64-ko.report.json

  python k64_localize.py reextract --rom "C:\Users\JO\Desktop\Hoshi no Kirby 64 (Japan) (Rev 3).z64" --candidate build\kirby64-ko.z64 --report build\kirby64-ko.report.json --out build\reextracted

수정 이미지와 글리프를 출력하며, 변경 범위와 체크섬도 확인합니다.
report 파일은 같은 빌드에서 생성된 것을 사용하세요.

무수정 왕복 확인

  python k64_localize.py roundtrip --rom "C:\Users\JO\Desktop\Hoshi no Kirby 64 (Japan) (Rev 3).z64" --workspace workspace

원본 자산을 새 작업 폴더에 다시 추출하려면

  python k64_localize.py extract --rom "C:\Users\JO\Desktop\Hoshi no Kirby 64 (Japan) (Rev 3).z64" --out fresh-workspace

검증 결과
993개 PNG와 두 글리프 아틀라스의 무수정 왕복에서 롬 전체 바이트 일치.
발견한 8종 이미지 형식의 픽셀 수정, 폰트와 ASCII 문자열을 함께 수정하는 빌드,
체크섬 갱신, 수정 롬의 재추출, 잘못된 크기/문자/길이/printf 인자 거부를 확인했습니다.
한글 '옵션'의 I4 삽입·재추출을 확인했으며, 시험 파일 정리 후에도 결과와 재현 방법은 codex-lab/knowledge/baseline.md에 보존합니다.

남은 확인
이 목록은 정적 리소스를 기준으로 합니다. 실제 표시 여부, 미사용/숨겨진 화면,
레이아웃·선택지·색상 상태는 에뮬레이터/실기에서 확인해야 합니다. 부팅 시험은 미실시입니다.
크래시 폰트 외의 독자 문자 인코딩/미확인 글리프 사용처는 조사 여지가 있습니다.
4,521개 이미지 블록 중 3,528개는 헤더 없는 텍스처/팔레트 등으로, 경계만 기록했으며
이 키트에서 PNG 편집 대상으로 확정하지 않았습니다. 전체 ROM 한글화 완료 목록을 뜻하지 않습니다.

참고 소스와 조사 범위는 sources.json에 기록했습니다.
