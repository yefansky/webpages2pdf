import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import queue
import pdfkit

class WebsiteCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.base_prefix = base_url.rstrip('/')  # 确保前缀一致
        self.visited = set()  # 用于记录已访问的URL
        self.queue = queue.Queue()  # BFS队列
        self.queue.put(base_url)
        self.visited.add(base_url)  # 初始URL标记为已访问
        self.all_pages = []  # 用于存储所有抓取的页面URL（BFS顺序）
        self.sorted_pages = []  # 用于存储按规则排序后的页面URL

    def is_same_prefix(self, url):
        # 检查URL是否以base_prefix开头
        return url.startswith(self.base_prefix)

    def is_html_page(self, url):
        # 检查URL是否是HTML页面（忽略JS、图片、CSS等）
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        # 常见的非HTML资源扩展名
        non_html_extensions = ['.js', '.jpg', '.jpeg', '.png', '.gif', '.css', '.svg', '.ico', '.pdf']
        return not any(path.endswith(ext) for ext in non_html_extensions)

    def get_links(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = set()
            for a_tag in soup.find_all('a', href=True):
                link = urljoin(url, a_tag['href'])
                # 去掉 # 部分
                link, _ = urldefrag(link)
                # 过滤掉不以base_prefix开头的链接，以及非HTML资源
                if self.is_same_prefix(link) and self.is_html_page(link) and link not in self.visited:
                    links.add(link)
            return links
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return set()

    def bfs(self):
        while not self.queue.empty():
            current_url = self.queue.get()
            print(f"Crawling: {current_url}")
            self.all_pages.append(current_url)  # 按照BFS顺序记录页面
            links = self.get_links(current_url)
            for link in links:
                if link not in self.visited:  # 确保未访问过的链接才入队
                    self.visited.add(link)  # 标记为已访问
                    self.queue.put(link)  # 加入队列

    def sort_pages(self):
        # 按照规则排序
        remaining_pages = self.all_pages.copy()  # 未输出的页面
        self.sorted_pages = []  # 排序后的页面

        while remaining_pages:
            if not self.sorted_pages:
                # 如果sorted_pages为空，选择第一个未输出的页面
                selected_page = remaining_pages.pop(0)
            else:
                # 获取最后一个输出的页面
                last_page = self.sorted_pages[-1]
                # 查找与last_page有相同前缀的页面
                selected_page = None
                for page in remaining_pages:
                    if page.startswith(last_page.rstrip('/') + '/'):
                        selected_page = page
                        break
                # 如果没有找到相同前缀的页面，选择第一个未输出的页面
                if not selected_page:
                    selected_page = remaining_pages.pop(0)
                else:
                    remaining_pages.remove(selected_page)
            self.sorted_pages.append(selected_page)

    def save_as_pdf(self, output_file):
        options = {
            'quiet': ''
        }
        pdfkit.from_url(self.sorted_pages, output_file, options=options)

if __name__ == "__main__":
    base_url = input("Enter the base URL: ").strip()
    output_pdf = "output.pdf"

    crawler = WebsiteCrawler(base_url)
    crawler.bfs()  # 使用BFS抓取
    crawler.sort_pages()  # 按照规则排序
    crawler.save_as_pdf(output_pdf)  # 保存为PDF

    print(f"PDF saved as {output_pdf}")