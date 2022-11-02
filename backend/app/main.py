from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from get_price import get_price_high


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
) 


@app.get("/{id}")
def read_price(id: int):
    return {id: get_price_high(id)} if id > 0 else {"default": get_price_high(id)}
 