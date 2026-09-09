# 실제 브라우저 실행 근거

일회용 DB·저장소·worker·viz와 agent-browser를 사용했다. 실제 원천 파일을 올렸으며 운영 데이터는 사용하지 않았다. 다운로드 원본 바이트는 실행 산출물에 있고 저장소에는 해시 대조 결과만 남긴다.

| 사례 | 원본 파일 | 바이트 | SHA256 | 완료 단계 |
|---|---|---:|---|---:|
| [tif-bundle](tif-bundle/journey.json) | HLS.S30.T51SYB.2025359T023019.v2.0.B02.tif | 24577705 | 2e883a8f031f4028c089e86edada93c51abc48540143e78cb6047c54c3eed258 | 7 |
| [nc](nc/journey.json) | gk2a_ami_le2_lst_ko_202005010000.nc | 397448 | 1cb901626ea6ea5c73eec6cd06af6f87a2d7984a68cecd0aaf1846952ee9571b | 6 |
| [hdf](hdf/journey.json) | MOD15A2H.A2019273.h27v05.061.2020313082826.hdf | 9731088 | ab7eda26634a5e2f13016acc7e1f8d0cd1daf3924bdbc58538b066b12c12e8a6 | 11 |
| [bin](bin/journey.json) | RDR_CMP_HSR_PUB_202508131000.bin.gz | 1259571 | 317500ebd261adbc3bbe4fe7a95bc69931d3f03ac96b84b97bc0b6fa05270456 | 6 |
| [bin-grid](bin-grid/journey.json) | RDR_CMP_HSR_PUB_202508131000.bin.gz | 1259571 | 317500ebd261adbc3bbe4fe7a95bc69931d3f03ac96b84b97bc0b6fa05270456 | 8 |
| [numpy](numpy/journey.json) | Prediction_20230501.npy | 6553728 | 7a5f0480e4dacf0911d3783631e9760c5d2e4b4a19888824bb12cbbc397eb392 | 8 |
| [grib](grib/journey.json) | surface.grib | 149514336 | 1b94e6d6756d90d239e3eb0ef763c9aa14f7395345bb49f4ffff87db90d39ba0 | 5 |

BIN은 좌표 없는 값 그림과 실제 기준 격자 첨부 두 사례를 구분한다. GRIB은 미리보기 성공이 아니라 명시적 제외 안내+등록/수정/원본 다운로드 성공이다. NumPy는 좌표배열을 본체로 꾸민 것이 아니라 Prediction 실사용 산출물에 LAT_crop/LON_crop을 붙인 사례다.

TIF 묶음은 B02·B03 2개 원본의 ZIP 개수·파일명·각 SHA256을 대조했다. HDF 최종 사례는 빠른 프로젝트 생성, 변수 행, 2019-09-30~2019-10-07 기간, 10분 간격, 계보 방법 수정·제거·재연결, 노드 이동, 상세 셀별 편집을 실제 저장 후 다시 조회했다.

[부분 실패 최종 실행](partial/journey.json): 실제 B02 TIF에 의도적으로 읽을 수 없는 TIF 한 개를 추가했다. 부분 그림·누락 원본명·저장/재조회·편집·좌표·개별/묶음 원본 해시 9단계 통과. 손상 파일은 오류 주입이며 실제 정상 원천 파일로 계산하지 않는다.
