# YES24 Library Status 0.3.6

- Calibre 시작 후 YES24 국내도서 스테디셀러 storefront를 백그라운드에서 수집합니다.
- 수집한 product `itemId` 집합을 `<Calibre config>/yes24_library_status/steady_seller.json`에 원자적으로 저장합니다.
- 갱신 실패 시 이전 정상 캐시를 보존하며 한 차례 지연 재시도합니다.
- Metadata Source 0.5.4가 이 공유 캐시를 사용해 `⭐스테디셀러` 태그를 추가합니다.
- startup storefront 요청에는 사용자의 EPUB/PDF, 제목, ISBN, `identifier:yes24`, 라이브러리 메타데이터를 전송하지 않습니다.

실환경 검증: Calibre 9.14 / Windows 11 / 3,776권 라이브러리에서 26페이지, 1,028 unique product IDs 수집 및 Metadata Source 연동을 확인했습니다.
