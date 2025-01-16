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
        # 按照URL的路径深度和字母顺序排序
        def get_path_depth(url):
            # 计算URL的路径深度（即路径中 '/' 的数量）
            parsed_url = urlparse(url)
            path = parsed_url.path
            return path.count('/')

        # 先按路径深度排序，再按字母顺序排序
        self.sorted_pages = sorted(self.all_pages, key=lambda x: (get_path_depth(x), x))

    def save_as_pdf(self, output_file):
        options = {
            'quiet': '',
        }
        # Path to the wkhtmltopdf binary
        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

        # Create a configuration object
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        pdfkit.from_url(self.sorted_pages, output_file, options=options, configuration=config)

if __name__ == "__main__":
    base_url = input("Enter the base URL: ").strip()
    output_pdf = "output.pdf"

    crawler = WebsiteCrawler(base_url)
    crawler.bfs()  # 使用BFS抓取
    crawler.sort_pages()  # 按照规则排序
    crawler.save_as_pdf(output_pdf)  # 保存为PDF

    print(f"PDF saved as {output_pdf}")