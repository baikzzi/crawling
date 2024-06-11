import aiohttp
import asyncio
from bs4 import BeautifulSoup
import aiofiles
import time
from concurrent.futures import ThreadPoolExecutor
import os

# 시작 숫자와 끝 숫자를 정의합니다.
start_num = 783522451
end_num = start_num + 100

# output 디렉터리가 존재하지 않으면 생성합니다.
output_dir = 'output'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

urls = [(num, f'https://www.daangn.com/articles/{num}') for num in range(end_num, start_num, -1)]

async def fetch_data(session, curr_num, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                raise ValueError(f"Failed to fetch {url}, status code: {response.status}")
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            item = soup.find('article')
            if not item:
                raise ValueError(f"Article not found in {url}")
            
            title = item.find('h1').get_text() if item.find('h1') else "Title not found"
            geturl = soup.select_one('meta[property="og:url"]')['content'] if soup.select_one('meta[property="og:url"]') else "URL not found"
            link = item.find('img', class_='portrait')['data-lazy'] if item.find('img', class_='portrait') else "Image link not found"

            text_filename = os.path.join(output_dir, f'dg_{curr_num}.txt')
            async with aiofiles.open(text_filename, 'w', encoding='utf-8') as text_file:
                await text_file.write(f'URL: {geturl}\n')
                await text_file.write(f'Title: {title}\n')
                await text_file.write(f'Image Link: {link}\n')

            if link != "Image link not found":
                image_extension = link.split('.')[-1].split('?')[0]  # 파일 확장자 추출
                image_filename = os.path.join(output_dir, f'dg_{curr_num}.{image_extension}')
                async with aiofiles.open(image_filename, 'wb') as image_file:
                    async with session.get(link, timeout=10) as img_response:
                        if img_response.status == 200:
                            image_data = await img_response.read()
                            await image_file.write(image_data)
                            print(f"이미지 저장 성공: {image_filename}")
                        else:
                            print(f"이미지 다운로드 실패: {link}, status code: {img_response.status}")

            return (geturl, title, link)
    except Exception as e:
        text_filename = os.path.join(output_dir, f'dg_{curr_num}.txt')
        async with aiofiles.open(text_filename, 'w', encoding='utf-8') as text_file:
            await text_file.write('URL: NONE\n')
            await text_file.write('Title: NONE\n')
        print(f"에러 발생: {url}, 에러: {e}")
        return (url, "NONE", "NONE")

async def main():
    start_time = time.time()

    max_workers = os.cpu_count() * 2
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop.set_default_executor(executor)

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=100)) as session:
            tasks = [fetch_data(session, curr_num, url) for curr_num, url in urls]
            results = await asyncio.gather(*tasks)

    end_time = time.time()

    print(f'시작 시간: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))}')
    print(f'종료 시간: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))}')
    print(f'총 소요시간: {end_time - start_time} 초')

if __name__ == '__main__':
    asyncio.run(main())
