from jinja2 import pass_environment
from numpy import str_
import requests 
from bs4 import BeautifulSoup
import sys 
import trio
import httpx

simultaneous_requests = trio.CapacityLimiter(5)


# download_directory
async def download_directory(url:str):
    response = await download_xml(url)
    #print(response.content)
    print(type(response))
    soup = BeautifulSoup(response, 'xml')

    bills = soup.data.files
    # links: list[Element]  = Array.from(bills.querySelectorAll('a'))
    links = (file.link for file in bills)
    # xml_links: filter[list[Element]] = links.filter(a => a.href.includes(".xml"))
    xml_links = (link for link in links if link.contents[0].endswith('xml'))
    # xml_urls: list[str] = xml_links.map(a => a.href)
    xml_urls = [link.contents[0] for link in xml_links]
    async with trio.open_nursery() as nursery:
        print(f'{len(xml_urls)=}')
        for link in xml_urls:
            nursery.start_soon(download_xml_and_save, link)
    print("completed!")

async def download_xml(url:str)->str:
    async with httpx.AsyncClient() as client:
        async with simultaneous_requests:
            r = await client.get(url, headers={"Accept":"application/xml"})
        r.raise_for_status()
        #print("I",end="")
        return r.content.decode()

async def download_xml_and_save(url:str):
    #print(url)
    response = await download_xml(url)
    soup = BeautifulSoup(response, 'xml')
    try:
        id = soup.bill["slc-id"]
    except:
        #print(response)
        print('X',end="",flush=True)
        return
    print("I",end="",flush=True)
    filename = f'data/{id}.xml' 
    with open(filename,'w') as f:
        f.write(response)



    






# munge_data
def munge_data():
    ...

# Dispatcher
# Operations [download_directory, munge_data]
# do operations
if __name__ == "__main__":
    if len(sys.argv) == 1:
        argv = ["download_directory", "https://www.govinfo.gov/bulkdata/BILLS/117/2/s"]
    else:
        argv = sys.argv[1:]
    operation = argv[0]
    if operation=="download_directory":
        trio.run(download_directory, argv[1])
