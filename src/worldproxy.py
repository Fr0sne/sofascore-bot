from requests import get
from bs4 import BeautifulSoup
import json
from base64 import b64decode


class Proxy:
    #PROTOCOLO://IP:PORT
    def __init__(self):
        self.proxies = []
        self.geonode()
        self.free_proxy_lists()
        self.hidemy()
        self.free_proxy_cz()
        # self.freeproxylist()
        self.proxies = list(dict.fromkeys(self.proxies))
        with open("proxies.txt", 'w+') as f:
            f.write("\n".join(self.proxies))
         
    def free_proxy_lists(self):
        url = "https://free-proxy-list.net/"
        proxyList = get(url, timeout=10).text
        soup = BeautifulSoup(proxyList, 'html.parser')
        for tr in soup.find_all('tr'):
            try:
                ip = tr.find_all('td')[0].string
                port = tr.find_all('td')[1].string
                protocol = "http" if tr.find_all('td')[6].string == "no" else "https"
                if not "-" in ip and len(ip) >= 7:
                    self.proxies.append(protocol + "://" + ip + ":" + port)
            except:
                pass
    def hidemy(self):
        url = "https://hidemy.name/en/proxy-list/?maxtime=1200&type=45#list"
        proxyList = get(url, timeout=10).text
        soup = BeautifulSoup(proxyList, 'html.parser')
        for tr in soup.find_all('tr'):
            try:
                ip = tr.find_all('td')[0].string
                port = tr.find_all('td')[1].string
                protocol = tr.find_all('td')[4].string
                self.proxies.append(protocol.lower() + "://" + ip + ":" + port)
            except:
                print("erro")
                pass
                
    def geonode(self):
        url = "https://proxylist.geonode.com/api/proxy-list?limit=200&page=1&sort_by=latency&sort_type=asc&speed=fast"
        try:
            proxyJson = json.loads(get(url).text)
            for proxy in proxyJson['data']:
                self.proxies.append("{}://{}:{}".format(proxy['protocols'][0], proxy['ip'], proxy['port']))
                
        except:
            print("Geonode não disponível, indo para o próximo site...")

    def free_proxy_cz(self):
        url = "http://free-proxy.cz/en/proxylist/country/BR/socks4/ping/all"
        proxyList = get(url).text
        soup = BeautifulSoup(proxyList, 'html.parser')
        for tr in soup.find_all('tr'):
            try:
                for td in tr.find_all('td'):
                    port = tr.find_all('td')[1].string
                    ip = td.find_all('script')
                    protocol = tr.find_all('td')[2].string.lower()
                    # print(target)
                    if len(ip) > 0:
                        buffer = ip[0].string.replace('document.write(Base64.decode("', '').replace('"))', '')

                        ip = b64decode(buffer).decode('utf-8')
                        print({'http': f"{protocol}://{ip}:{port}", 'https' : f"{protocol}://{ip}:{port}"})
                        self.proxies.append(f"{protocol}://{ip}:{port}")

                    # print(td)
            except:
                print("Free Proxy Cz não está disponível")
                pass

