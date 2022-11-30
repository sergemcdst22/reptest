from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import aiofiles
from PIL import Image, ImageFont, ImageDraw 

from get_price import get_price_high


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
) 


@app.get("/read_price/{id}")
def read_price(id: int):

    price, time, name = get_price_high(id)
    old_name = "?"
    last_price = None
    lines = []
    try:
        with open(f"art{id}.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_price = lines[1].split(" --- ")[0] 
            old_name = lines[0] 
    except:
        ...

    try:
        if not last_price or str(last_price) != str(price) and len(lines) > 0:

            with open(f"art{id}.txt", "w", encoding="utf-8") as f:
                f.writelines([lines[0]] + [f"{price} --- {time}\n"] + lines[1:])
        
        if old_name == "?" and name != "?":

            with open(f"art{id}.txt", "w", encoding="utf-8") as f:
                f.writelines([f"{name}\n"] + lines[1:])

        
    except:
        ...

    return price, time, name



@app.get("/articules")
def show_all_ids():
    try:
        with open("list.txt", "r") as f:
            return f.readlines()
    except:
        return []


@app.get("/articules/{id}")
def read_article_file(id: int):
    try:
        with open(f"art{id}.txt", "r", encoding="utf-8") as f:
            return f.readlines()
    except:
        return None


@app.delete("/articules/{id}")
def delete_article(id: int):
    try:
        with open("list.txt", "r") as f:
            articules = set([int(l) for l in f.readlines()])
        if id in articules:
            articules.remove(id)
        new_articules = [f"{a}\n" for a in articules]
        with open("list.txt", "w+") as f:
            f.writelines(new_articules)
        try:
            os.remove(f"art{id}.txt")
        except:
            ...
        return new_articules
    except:
        return []


@app.get("/addarticule/{id}")
def add_new_id(id: int):
    articules = set()
    try:
        with open("list.txt", "r") as f:
            articules = set([int(l) for l in f.readlines()])
    except: 
        ...
    if not id in articules:
        articules.add(id)
        try:
            os.remove(f"art{id}.txt")
        except OSError:
            ...
        with open(f"art{id}.txt", 'x', encoding="utf-8"):
            ... 
        try:
            price, time, name = read_price(id)
            with open(f"art{id}.txt", 'w', encoding="utf-8") as f:
                f.writelines([f"{name}\n"] + [f"{price} --- {time}\n"])
        except Exception as e:
            print(e)
    new_articules = [f"{a}\n" for a in articules]
    with open("list.txt", "w+") as f:
        f.writelines(new_articules)
    return new_articules


def is_following(d):
    return d and type(d) is dict and d["total"] > 0 and str(d['data'][0]['followed_at'])[:10]


def is_subscribed(d):
    return d and type(d) is dict and not 'error' in d


@app.get("/atg/{id}")
async def read(id):
    txt = ''

    try:
        async with aiofiles.open(f"{id}.txt", mode='r') as f:
            txt = await f.read()  
    except:
        ...

    return txt  
        



@app.get("/atg")
async def save_atg(code: str, scope: str, state: str):

    async with httpx.AsyncClient() as client:

        client_id = 'lfe9vvdv7dihqm4e6i4dr4elon2gvk'
        client_secret = 'jidrdopja5f4savde4nhe4a0n6mpn1'
        redirect_uri = 'https://api.rep-test.ru/atg'

        aninya_id = '163110751'

        r = await client.post('https://id.twitch.tv/oauth2/token', 
            headers={'Content-Type': 'application/x-www-form-urlencoded'}, 
            data=f'{client_id=!s}&{client_secret=!s}&{code=!s}&grant_type=authorization_code&{redirect_uri=!s}')
         

        token = r.json()["access_token"]

        r = await client.get('https://id.twitch.tv/oauth2/validate', headers={'Authorization': f'OAuth {token}'})

        user_data = r.json()
 

        r = await client.get(f'https://api.twitch.tv/helix/users/follows?to_id={aninya_id}&from_id={user_data["user_id"]}',
            headers={'Authorization': f'Bearer {token}', 'Client-Id': f'{client_id}'})

        user_is_following = is_following(r.json())

        r = await client.get(f'https://api.twitch.tv/helix/subscriptions/user?broadcaster_id={aninya_id}&user_id={user_data["user_id"]}',
            headers={'Authorization': f'Bearer {token}', 'Client-Id': f'{client_id}'})
            
        user_is_subscribed = is_subscribed(r.json())

        async with aiofiles.open(f'{state}.txt', mode='w') as f:
            await f.write(f"{user_data['login']} {user_is_following} {user_is_subscribed}")

        
        return f"{user_data['login']}, благодарим за регистрацию. Скоро вам придет ссылка от бота"

def wrap(s_g: str, max_len: int):
    spl = s_g.split()
    results = [""]
    i = 0
    cur_len = 0
    for s in spl:
        if cur_len + len(s) < max_len:
            results[i] += " " + s
            cur_len += len(s)
        else:
            results[i] = results[i].strip()
            results.append(s)
            i += 1
            cur_len = 0

    results[-1] = results[-1].strip()

    return results

def fill_template(anketa_imya, anketa_familia, anketa_webinar: str):
    name = f"{anketa_familia} {anketa_imya}"


    anketa_webinar = anketa_webinar.split('Лектор')

    lector_name = anketa_webinar[-1].strip()

    anketa_webinar = anketa_webinar[0].strip()

    date = anketa_webinar[-8:]

    anketa_webinar = anketa_webinar[:-8].strip()

    anketa_webinar = anketa_webinar.split(".")

    for i in range(len(anketa_webinar)):
        s = anketa_webinar[i].strip()
        if len(s) > 50:
            s = "\n".join(wrap(s, 40))
        anketa_webinar[i] = s

    anketa_webinar = ".\n".join(anketa_webinar)

    my_image = Image.open("template.png")
    font = ImageFont.truetype('MYRIADPRO-BOLD.OTF', 26, encoding='utf-8')  
    font2 = ImageFont.truetype('MYRIADPRO-REGULAR.OTF', 17, encoding='utf-8') 
 
    image_editable = ImageDraw.Draw(my_image)
    image_editable.text((80, 325), name, (0, 0, 0), font=font)
    image_editable.text((80, 423), anketa_webinar, (0, 0, 0), font=font)
    image_editable.text((80, 633), lector_name, (255, 255, 255), font=font)
    image_editable.text((127, 744), date, (255, 255, 255), font=font2)
    my_image.save("result.png")
 

    
@app.get("/course_cert")
def save_atg(anketa_imya: str, anketa_familia: str, anketa_webinar: str):
    fill_template(anketa_imya, anketa_familia, anketa_webinar)
    return FileResponse("result.png")


 