from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

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

    price, time, name =  get_price_high(id)
    old_name = "?"
    last_price = None
    lines = []
    try:
        with open(f"art{id}.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_price = lines[1].split(" --- ")[0]
            old_name = lines[0]
            print(name)
    except:
        ...

    try:
        if not last_price or last_price != price and len(lines) > 0:

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


@app.post("/articules/")
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



 