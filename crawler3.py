import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

# 저장 디렉토리 설정
if not os.path.exists('output'):
    os.makedirs('output')

# 시작 상품 번호와 상품 수 설정
start_num = 783022451
product_count = 100

# URL 목록 생성 함수
def generate_urls(start_num, count):
    return [f'https://www.daangn.com/articles/{start_num + i}' for i in range(count)]

# 데이터 추출 함수
def fetch_data(session, url):
    try:
        response = session.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            item = soup.find('article')
            title = item.find('h1').get_text()
            geturl = soup.select_one('meta[property="og:url"]')['content']
            link = item.find('img', class_='portrait')['data-lazy']

            # 파일명 생성
            product_id = geturl.split("/")[-1]
            base_filename = f'output/dg-{product_id}'

            # 텍스트 저장 (확장자 없이)
            text_filename = base_filename
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write(f'Title: {title}\nURL: {geturl}')

            return (geturl, title, link, base_filename)
        else:
            print(f'웹페이지 로드 실패  {url}. Status code: {response.status_code}')
            return (None, None, None, None)
    except Exception as e:
        print(f'에러 발생: {url}, 에러: {e}')
        return (None, None, None, None)

# 이미지 다운로드 함수
def download_image(session, link, img_filename):
    try:
        img_data = session.get(link).content
        with open(img_filename, 'wb') as handler:
            handler.write(img_data)
    except Exception as e:
        print(f'이미지 다운로드 실패: {link}, 에러: {e}')

# 병렬 처리를 사용하여 데이터를 빠르게 추출합니다.
urls = generate_urls(start_num, product_count)

# 시작 시간을 기록합니다.
start_time = time.time()

with ThreadPoolExecutor(max_workers=10) as executor:
    with requests.Session() as session:
        futures = {executor.submit(fetch_data, session, url): url for url in urls}
        img_futures = []

        for future in as_completed(futures):
            geturl, title, link, base_filename = future.result()
            if geturl and title and link and base_filename:
                img_futures.append(executor.submit(download_image, session, link, f'{base_filename}.jpg'))

        # 이미지 다운로드 완료 대기
        for img_future in as_completed(img_futures):
            img_future.result()

# 종료 시간을 기록합니다.
end_time = time.time()
# 시작 시간과 종료 시간을 출력합니다.
print(f'시작 시간: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))}')
print(f'종료 시간: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))}')
print(f'총 소요시간: {end_time - start_time} 초')