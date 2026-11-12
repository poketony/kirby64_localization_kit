# 한국어 글자 모델

현재 두 모델은 모두 사용자 제공 PNG의 윤곽으로 제작해 ROM에 반영했다. 폰트 파일은 사용하지 않았다. PNG 이미지 b3_0005/b3_0006과는 별개다.

| 모델 | 문구 | 제작원 | 크기 |
|---|---|---|---|
| geo_b3_0005.bin | 형편없네요 | workspace/artwork/geometry-27/geo_b3_0005-source.png | 21,152바이트 |
| geo_b3_0006.bin | 축하합니다! | workspace/artwork/geometry-28/geo_b3_0006-source.png | 20,720바이트 |

최신 ROM: `build/kirby64-ko-graphics-20261112-v3.z64`. 기존 PNG 350개도 유지한다. 두 모델 모두 기존 노드·애니메이션 참조·재질 및 최종 상태 복구 명령을 보존했다. 빈 ROM 패딩에 배치한 것이므로 원본 슬롯에 직접 덮어쓰지 않는다.

저장 후 모델 재추출·체크섬·변경 범위 검사를 통과했다. 실제 게임 애니메이션은 아직 미검증이다.

[형편없네요 적용](../../../codex-lab/knowledge/failure-image-27.md) · [축하합니다! 적용](../../../codex-lab/knowledge/success-image-28.md).
