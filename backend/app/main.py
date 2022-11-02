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

    last_price = None
    lines = []
    try:
        with open(f"art{id}.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_price = lines[0].split(" --- ")[0]
    except:
        ...

    try:
        if not last_price or last_price != price:
            with open(f"art{id}.txt", "w", encoding="utf-8") as f:
                f.writelines([f"{price} --- {time} --- {name}\n"] + lines)
    except:
        ...

    return price, time, name



@app.get("/articules")
def show_all_ids():
    with open("list.txt", "r") as f:
        return f.readlines()


@app.get("/articules/{id}")
def read_article_file(id: int):
    try:
        with open(f"art{id}.txt", "r", encoding="utf-8") as f:
            return f.readlines()
    except:
        return None


@app.delete("/articules/{id}")
def delete_article(id: int):
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


@app.post("/articules/{id}")
def add_new_id(id: int):
    try:
        with open("list.txt", "r") as f:
            articules = set([int(l) for l in f.readlines()])
    except: 
        ...
    if not id in articules:
        articules.add(id)
        with open(f"art{id}.txt", 'x', encoding="utf-8"):
            ...
        try:
            price, time, name = read_price(id)
            with open(f"art{id}.txt", 'w', encoding="utf-8") as f:
                f.writelines([f"{price} --- {time} --- {name}\n"])
        except:
            ...
    new_articules = [f"{a}\n" for a in articules]
    with open("list.txt", "w+") as f:
        f.writelines(new_articules)
    return new_articules



 