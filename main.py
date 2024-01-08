import re
import sys
from urllib.parse import urlparse
import requests

from bs4 import BeautifulSoup
import json

WHEN_TO_CHOOSE_URL = 'https://dev6.cloudzy.com/api/v1/images/landing_whenToChoose'

def innerHTML(html_tag):
    text = ""
    for c in html_tag.contents:
        text+=str(c)
    return text

def scrape_url_to_json(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
    except requests.RequestException as e:
        return f"Error: Unable to access the URL due to {e}"

    soup = BeautifulSoup(response.text.replace('\u2019',"'"), 'html.parser')
    scraped_data = {
        "seo": {},
        "hero": {}
    }
    """
    scraped_data = {
        "seo": {},
        "heroSection": {},
        "pricing": {},
        "introduction": {},
        "platforms": {},
        "whatOperatingSystems": {},
        "featuresCarousel": {},
        "paymentMethods": {},
        "testimonial": {},
        "whenToChoose": {},
        "whyChoose": {},
        "cta": {},
        "FAQ": {}
        }
    """

    # Scrape data for SEO
    # This is an example and may need to be adjusted based on the actual page structure
    scraped_data["seo"]["title"] = soup.title.string if soup.title else "Title not found"
    scraped_data["seo"]["description"] = soup.find('meta', property="og:description").attrs["content"]
    
    scraped_data["seo"]["og"] = {
        "title": soup.find('meta', property="og:title").attrs["content"],
        "description": soup.find('meta', property="og:description").attrs["content"],
        "url": soup.find('meta', property="og:url").attrs["content"],
        "image:alt": soup.find('meta', property="og:image:alt").attrs["content"],
        "image": soup.find('meta', property="og:image").attrs["content"],
        "image:width": int(soup.find('meta', property="og:image:width").attrs["content"]),
        "image:height": int(soup.find('meta', property="og:image:height").attrs["content"]),
        "image:type": soup.find('meta', property="og:image:type").attrs["content"],
        "yandex": soup.find('meta', attrs={'name': 'yandex-verification'}).attrs["content"]
    }
        
    # SCHEMA
    script_tags = soup.find_all('script', {'type': 'application/ld+json'})
    scraped_data["seo"]["schema"] = []
    
    for script in script_tags:
        json_data = json.loads(script.get_text())
        scraped_data["seo"]["schema"].append(json_data)
        
    # Scrape data for Hero Section
    # This is an example and may need to be adjusted based on the actual page structure
    typical_hero =  soup.find("h1",
                                                     class_="MuiTypography-root MuiTypography-h6 css-1ng44mv")
    if typical_hero:
        scraped_data["hero"]["title"] = soup.find("h1",
                                                     class_="MuiTypography-root MuiTypography-h6 css-1ng44mv").text
        scraped_data["hero"]["description"] = soup.find("h2",
                                                           class_="MuiTypography-root MuiTypography-h1 css-hacks1").text
        scraped_data["hero"]["image"] = {}
        scraped_data["hero"]["image"]["src"] = "https://dev6.cloudzy.com/static/hero/default.webp"
        scraped_data["hero"]["image"]["alt"] = "hero"
        scraped_data["hero"]["subDescription"] = soup.find("p",
                                                              class_="MuiTypography-root MuiTypography-h6 css-1ng44mv").text
        scraped_data["hero"]["features"] = []
        features = soup.find('div', class_="MuiPaper-root MuiPaper-elevation MuiPaper-rounded MuiPaper-elevation1 MuiCard-root css-1uu4fvx")
        performanceFeatures = features.find_all('div', 'MuiGrid-root MuiGrid-container css-11hqo0i')
        for index, performanceFeature in enumerate(performanceFeatures):
            dic = {
                "title": performanceFeature.find_all('p')[0].text,
                "description": performanceFeature.find_all('p')[1].text
            }
            if "Experience" in dic["description"]:
                dic["image"] = {
                    "src": "https://dev6.cloudzy.com/static/hero/features/suitcase.webp",
                    "alt": "experience"
                }
            if "Money-Back Guarantee" in dic["description"]:
                dic["image"] = {
                "src": "https://dev6.cloudzy.com/static/hero/features/shield.webp",
                "alt": "refund option"
                }
            if "Online Support" in dic["description"]:
                dic["image"] = {
                "src": "https://dev6.cloudzy.com/static/hero/features/headphone.webp",
                "alt": "support"
                }
            if "Created VPS" in dic["description"]:
                dic["image"] = {
              "src": "https://dev6.cloudzy.com/static/hero/features/server.webp",
              "alt": "person"
                }
            if "Uptime" in dic["description"]:
                dic["image"] = {
                "src": "https://dev6.cloudzy.com/static/hero/features/refund.webp",
                "alt": "uptime"
                }
            scraped_data["hero"]["features"].append(dic)
            
    action_text = soup.find("span", class_="MuiTypography-root MuiTypography-buttonLarge css-a68wbd").text
    if (action_text):
        scraped_data["hero"]["action"] = {
            "content": ""
        }
        scraped_data["hero"]["action"]["content"] = action_text

    features_div = soup.find('div', class_='MuiGrid-root MuiGrid-container css-71qxqu')
    if features_div:
        scraped_data["introduction"] = {
            "features": []
        }
        for div in features_div.children:
            title = div.find('p', class_={re.compile('MuiTypography-root MuiTypography-h6.*')}).text
            description = div.find('p', class_={re.compile('MuiTypography-root MuiTypography-body2.*')}).text
            scraped_data["introduction"]["features"].append({
                'title': title,
                'description': description
            })

    pricing_div = soup.find('div', class_="flex flex-col items-center pt-24 sm:pt-32 md:pt-36")
    if (pricing_div):
        scraped_data["pricing"] = {}
        toggle_div = pricing_div.find('div', class_="select-none")
        if toggle_div:
            for anchor in toggle_div.findAll('a'):
                scraped_data["pricing"][anchor.text] = []
        else:
            parsed_url = urlparse(scraped_data["seo"]["og"]["url"])
            path_components = parsed_url.path.split('/')
            slug = next((comp for comp in reversed(path_components) if comp), None)
            scraped_data["pricing"][slug] = []
        for index, (key, value) in enumerate(scraped_data["pricing"].items()):
            #plan spec
            plantable_div = pricing_div.findAll('div', class_="grid grid-cols-1 items-end gap-5 sm:grid-cols-2 lg:grid-cols-4")
            for card in plantable_div[index].find_all('div', class_="flex flex-col rounded-lg bg-primary-light"):
                card_dic = {}
                card_dic["planSpec"] = []
                header = card.find('div', class_="flex flex-col justify-center")
                additional_classes = {"text-text-primary", "text-white-default"}
                all_divs = card.find_all('div', class_=re.compile("flex items-center pt-2.*"))
                filtered_rows = [row for row in all_divs if any(cls in row.get('class', []) for cls in additional_classes)]
                for row in filtered_rows:
                    if header:
                        card_dic["title"] = header.find_all('p')[0].text
                        card_dic["subtitle"] = header.find_all('p')[1].text
                        row_dic = {}
                        row_dic["title"] = row.find_all('p')[0].text
                        row_dic["description"] = row.find_all('p')[1].text
                        card_dic["planSpec"].append(row_dic)
                #most_popular or not
                card_dic["isPopular"] = False
                card_dic["isCustom"] = False
                card_dic["isActive"] = True
                if card.find('button', class_="cursor-default bg-grey-200 text-grey-400 border-0 w-full px-5 py-2 rounded px-4 py-1.5 font-sans text-buttonSmall transition duration-300"):
                    card_dic["isActive"] = False
                card_dic["image"] = {
                    #hardcoded example
                    "src": "https://dev6.cloudzy.com/static/pricing/linux.webp" if len(card_dic["planSpec"]) > 0 and card_dic["planSpec"][0]["title"] == "1 GB" else "https://dev6.cloudzy.com/static/pricing/windows.webp",
                    "alt": "linux" if len(card_dic["planSpec"]) > 0 and card_dic["planSpec"][0]["title"] == "1 GB" else "windows"
                }
                if (card.find('p', class_='text-center text-subtitle1 text-primary-main')):
                    card_dic["isPopular"] = True
                    
                paragraph = card.find(lambda tag: tag.name == "p" and "Custom " in tag.text)
                if (paragraph):
                    card_dic["isCustom"] = True
                    card_dic["isPopular"] = False
                    card_dic["title"] = 'Can’t find what you’re looking for? Contact us and make your own!'
                    card_dic["subtitle"] = ''
                    card_dic["planSpec"] = [{
                        "title": "Custom",
                        "description": "DDR4 Memory"
                    },
                    {
                        "title": "Custom",
                        "description": "High-end 3.2+ GHz"
                    },
                    {
                        "title": "Custom",
                        "description": "NVMe/SSD Storage"
                    },
                    {
                        "title": "Custom",
                        "description": "Bandwidth"
                    },
                    {
                        "title": "Up to Custom",
                        "description": "Connections"
                    }]
               
                if (card_dic["isPopular"] == True):
                    card_dic["bookmarkText"] = "Most Popular"
                if (card_dic["isCustom"] == True):
                    card_dic["bookmarkText"] = "Make your own plan"
               
                if (card.find('div', class_="flex flex-col items-center")):
                    card_dic["pricing"] = {
                        "perMonth": {},
                        "perHour": {},
                        "unit": "$"
                    }
                    card_dic["pricing"]["perMonth"] = {
                        "price": float(card.find('span', class_="ml-1 text-h3").text),
                        "period":'m'
                    }
                    card_dic["pricing"]["perHour"] = {
                        "price": "",
                        "period": "h"
                    }
                    hourly_price = card.find('div', class_="mt-2 min-h-[21px] w-full").find_all('p')
                    if hourly_price:
                        card_dic["pricing"]["perHour"]["price"] = float(hourly_price[1].text[1:-1])
                    else:
                        card_dic["pricing"]["perHour"]["price"] = ""
                scraped_data["pricing"][key].append(card_dic)

    intro_div = soup.find('div', class_="MuiGrid-root MuiGrid-container css-1c87emg")
    if intro_div:
        scraped_data["introduction"] = {
            "description": intro_div.find('p', class_={
            re.compile("MuiTypography-root MuiTypography-body1.*")}).text,
            "title": intro_div.find('h2', class_={
            re.compile("MuiTypography-root MuiTypography-h2.*")}).text,
            "featureIcon": {"src": "https://dev6.cloudzy.com/static/common/feature-checkmark.webp",
                    "alt": "check mark"},
            "image":  {
                "src":"",
                "alt":""    
                },
            "features": []
        }      
        scraped_data["introduction"]["features"] = []
        for div in intro_div.find('div', class_="MuiGrid-root MuiGrid-container css-cpkics").find_all('p'):
            scraped_data["introduction"]["features"].append(div.text)

    suspected_platforms_divs = []
    platforms_div = soup.find('div', class_ ='css-4we2yn')
    second_platforms_div = soup.find('div', class_ ='css-1ai1zlu')
    suspected_platforms_divs.append(platforms_div)
    suspected_platforms_divs.append(second_platforms_div)

    for div in suspected_platforms_divs:
        h2_tag = div.find('h2')
        if div and h2_tag and 'FAQ' not in h2_tag.text and 'What' not in h2_tag.text:
            selected_div = div
            scraped_data["platforms"] = {}
            scraped_data["platforms"]["title"] = selected_div.find('h2').text
            scraped_data["platforms"]["platforms"] = []
            scraped_data["platforms"]["platformImageSize"] = {
                "width": "220",
                "height": "80"
            }
            items = platforms_div.findAll('div', class_="css-19kzrtu")
            if len(items) == 0:
                items = second_platforms_div.findAll('div', class_="css-19kzrtu")
            for div in items:
                dic = {}
                dic["description"] = innerHTML(div.find('p'))
                dic["image"] = { "alt": "", "src": ""}
                scraped_data["platforms"]["platforms"].append(dic)                
    
    why_choose_div = soup.find('div', class_='css-u27sdv')
    if why_choose_div:
        scraped_data["whyChoose"] = {}
        scraped_data["whyChoose"]["title"] = why_choose_div.find('h2').text
        scraped_data["whyChoose"]["action"] = {
            "link": why_choose_div.find('a').get('href'),
            "content": why_choose_div.find('span',class_='css-a68wbd').text
        }
        scraped_data["whyChoose"]["items"] = []
        for div in why_choose_div.find('div',class_="css-15j76c0").find_all('div',class_={re.compile("css-pjvi1b.*")}):
            dic = {
                "title": div.findAll('p')[0].text,
                "image": { "src": '', "alt": ""},
                "description": innerHTML(div.findAll('p')[1])
            }
            scraped_data["whyChoose"]["items"].append(dic)
    
    what_os_div = soup.find('div', class_="css-90epzu")
    if what_os_div:
        scraped_data["whatOperatingSystems"] = {}
        scraped_data["whatOperatingSystems"]["title"] = what_os_div.find('h2').text
        scraped_data["whatOperatingSystems"]["description"] = innerHTML(what_os_div.find('p'))
        scraped_data["whatOperatingSystems"]["images"] = []
        for div in what_os_div.find('div', class_="css-z99kbh").find_all("div", class_={re.compile("css-1angkc0")}):
            dic = {}
            dic["src"] = div.find('img').get('data-src') or div.find('img').get('src')
            dic["alt"] = div.find('img').get('alt')    

    coursel_div = soup.find('div', class_="MuiGrid-root MuiGrid-container MuiGrid-spacing-xs-4 css-24munp")
    if coursel_div: 
        scraped_data["featuresCarousel"] = {}
        scraped_data["featuresCarousel"]["title"] = coursel_div.find('h2', class_={
            re.compile("MuiTypography-root MuiTypography-h2.*")}).text
        scraped_data["featuresCarousel"]["description"] = coursel_div.find('span', class_={
            re.compile("MuiTypography-root MuiTypography-Body1.*")}).text
        scraped_data["featuresCarousel"]["features"] = []
        for index, div in enumerate(coursel_div.find('div',
                                    class_="MuiGrid-root MuiGrid-container MuiGrid-spacing-xs-1 css-9y62yf").find_all('div',
                                                                                                                  class_={
                                                                                                                      re.compile(
                                                                                                                              "slick-slide.*")})):
            dic = {}
            titles = [feature["title"] for feature in scraped_data["featuresCarousel"]["features"]]
            if (div.find('h3').text not in titles):
                dic["title"] = div.find('h3').text
                dic["description"] = div.find('p').text
                dic["image"] = {
                    "src": "",
                    "alt": ""
                }
                if 'High' in div.find('h3').text:
                    image_src = "https://dev6.cloudzy.com/static/landing/featureCarousel/server.png"
                    image_alt = "server"
                elif 'Support' in div.find('h3').text:
                    image_src = "https://dev6.cloudzy.com/static/landing/featureCarousel/headphone.png"
                    image_alt = "headphone"
                elif 'Risk-Free' in div.find('h3').text:
                    image_src = "https://dev6.cloudzy.com/static/landing/featureCarousel/wallet.png"
                    image_alt = "wallet"
                else:
                    image_src = "https://dev6.cloudzy.com/static/landing/featureCarousel/shield.png"
                    image_alt = "shield"
                dic["image"] = {
                    "src": image_src,
                    "alt": image_alt
                }
                scraped_data["featuresCarousel"]["features"].append(dic)

    potential_faq_divs = soup.find_all('div', class_="MuiGrid-root MuiGrid-container MuiGrid-spacing-xs-4 css-4we2yn")
    faq_div = potential_faq_divs[1] if len(potential_faq_divs) > 1 else potential_faq_divs[0]
    if len(potential_faq_divs) > 0:
        scraped_data["FAQ"] = {
            "iconType": "minusAndPlus"
        }
        scraped_data["FAQ"]["title"] = faq_div.find('h2').text
        scraped_data["FAQ"]["items"] = []
        for div in faq_div.find_all('div', class_=re.compile("css-dgmh43*.")):
            dic = {}
            dic["title"] = div.find('h3').text
            dic["description"] = innerHTML(div.find('p'))
            scraped_data["FAQ"]["items"].append(dic)
     
    payments_div = soup.find('div', class_="css-1pch3j1")
    if payments_div:
        scraped_data["paymentMethods"] = {}
        scraped_data["paymentMethods"]["title"] = payments_div.find("h2").text
        scraped_data["paymentMethods"]["image"] = { "src": "", "alt": "" }
        scraped_data["paymentMethods"]["methods"] = []
        scraped_data["paymentMethods"]["footerImages"] = [
        { "src": 'https://svgur.com/i/ztv.svg', "alt": 'cryptocurrency' },
        { "src": 'https://svgur.com/i/ztv.svg', "alt": 'cryptocurrency' },
        { "src": 'https://svgur.com/i/ztv.svg', "alt": 'cryptocurrency' },
        { "src": 'https://svgur.com/i/ztv.svg', "alt": 'cryptocurrency' },
        { "src": 'https://svgur.com/i/ztv.svg', "alt": 'cryptocurrency' }]
        for div in payments_div.find('div', class_="css-1z00lyu").find_all('div', class_={re.compile("css-lgz1qr.*")}):
            dic = {}
            dic["title"] = div.findAll('p')[0].text
            dic["description"] = div.findAll('p')[1].text
            dic["image"] = { "src": "", "alt": "" }
            scraped_data["paymentMethods"]["methods"].append(dic) 
            
    test_div = soup.find('div', class_="css-g9zy5h")
    if test_div:
        scraped_data["testimonial"] = {}
        scraped_data["testimonial"]["title"] = test_div.find('h2').text
        scraped_data["testimonial"]["slides"] = []
        for div in test_div.find('div', class_="slick-track").find_all('div', class_={re.compile("slick-slide.*")}):
            dic = {}
            dic["comment"] = div.findAll('p')[0].text
            dic["writerInfo"] = {"name": div.findAll('p')[1].text, "image": {"src":"", "alt": ""}}
            if ("Devan" in dic["writerInfo"]["name"]):
                dic["writerInfo"]["image"] = {
                        "src": "https://dev6.cloudzy.com/static/testimonial/devan-hartman.webp",
                        "alt": "some random guy's face"
                }
            if ("Immanuel" in dic["writerInfo"]["name"]):
                dic["writerInfo"]["image"] = {
                    "src": "https://dev6.cloudzy.com/static/testimonial/immanuel-webster.webp",
                    "alt": "some random guy's face"
                }
            if ("Donavan" in dic["writerInfo"]["name"]): 
                dic["writerInfo"]["image"] = {
                        "src": "https://dev6.cloudzy.com/static/testimonial/donnovan-kane.webp",
                        "alt": "some random guy's face"
                    } 
            if ("Reynaldo" in dic["writerInfo"]["name"]):
                dic["writerInfo"]["image"] = {
                    "src": "https://dev6.cloudzy.com/static/testimonial/reynaldo-duncan.webp",
                    "alt": "some random guy's face"
                    }
            if ("Diya" in dic["writerInfo"]["name"]):
                dic["writerInfo"]["image"] = {
                    "src": "https://dev6.cloudzy.com/static/testimonial/diya-dean.webp",
                    "alt": "some random girl's face"
                }
            dic["rating"] = len(div.find_all('span', class_="css-13m1if9"))
            scraped_data["testimonial"]["slides"].append(dic)

    when_div = soup.find('div', class_="MuiGrid-root MuiGrid-container MuiGrid-spacing-xs-4 css-1dny6fw")
    if when_div:
        scraped_data["whenToChoose"] = {
            "iconType": "arrows"
        }
        scraped_data["whenToChoose"]["image"] = {
            "src": "https://dev6.cloudzy.com/static/landing/whyChoose/background.webp",
            "alt": "guy behind laptop"
        }
        scraped_data["whenToChoose"]["title"] = when_div.find('h2').text
        scraped_data["whenToChoose"]["items"] = []
        for div in when_div.find_all('div', class_=re.compile("MuiPaper-root MuiPaper-elevation MuiPaper-rounded.*")):
            dic = {}
            dic["title"] = innerHTML(div.find('h3'))
            dic["description"] = innerHTML(div.find('p'))
            dic["icon"] = str(div.find('svg'))
            # title = dic["title"] + '.svg'
            # with open(title, 'w') as file:
            #     file.write(str(div.find('svg')))
            # with open(title, 'rb') as f:
            #     files = {
            #         'image': (title, f)
            #     }
            #     r = requests.post(WHEN_TO_CHOOSE_URL, files=files)
            # dic["image"] = {
            #     "alt": "icon image",  
            #     "src": "https://dev6.cloudzy.com/static/landing/whenToChoose/{}.svg".format(dic["title"])
            # }
            scraped_data["whenToChoose"]["items"].append(dic)

    cta_div = soup.find('div', class_="MuiGrid-root MuiGrid-container css-1jj7jpf")
    if cta_div:
        scraped_data["cta"] = {}
        scraped_data["cta"]["title"] = cta_div.find('h2').text
        scraped_data["cta"]["description"] = cta_div.find('p').text

    return scraped_data


if __name__ == '__main__':
    # URL to scrape
    url = 'https://cloudzy.com/windows-vps/' if len(sys.argv) <= 1 else sys.argv[1]
    # Scrape the URL and get JSON
    result = scrape_url_to_json(url)
    # Print or save the JSON
    with open(sys.argv[1].split('/')[-1]+".json", 'w') as file:
        json.dump(result, file, indent=4)
    #print(json.dumps(result, indent=4))
