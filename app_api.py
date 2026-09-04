import re
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json

from verified_rag import VerifiedLegalRAG
from alert_engine import LegalAlertEngine
from knowledge_graph import LegalKnowledgeGraph
from pdf_parser import LegalPDFParser
from vietlex_client import VietLexClient
from legal_precedence_engine import LegalPrecedenceEngine
from config import UPLOAD_DIR
from vector_store import LegalVectorStore

app = FastAPI(
    title="HACOM Legal Copilot API & Dashboard",
    description="Hệ thống Tra cứu Pháp lý có Kiểm chứng & Cảnh báo Tác động cho HACOM Holdings",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount HACOM logo images directory
images_dir = r"C:\KHMT\HacomHoldings\HacomKTKT\images"
if os.path.exists(images_dir):
    app.mount("/images", StaticFiles(directory=images_dir), name="images")

rag_engine = VerifiedLegalRAG()
alert_engine = LegalAlertEngine()
kg = LegalKnowledgeGraph()
vector_store = LegalVectorStore()
vietlex_client = VietLexClient()
precedence_engine = LegalPrecedenceEngine()

class LegalQueryRequest(BaseModel):
    question: str
    project_type: Optional[str] = "Chung"

class AlertRequest(BaseModel):
    doc_number: str
    doc_title: str
    field: Optional[str] = "Đất đai"

HTML_DASHBOARD = """<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HACOM Legal Copilot | Trợ lý Pháp lý Tập đoàn HACOM Holdings</title>
    <link rel="icon" type="image/png" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAKAAAAB6CAYAAAA4alhkAAAtIElEQVR42u29e3RdR5kn+vtV1d7noZf18Eu2E9uJHccOdMABgpNgOyQ4TkJPdzMyMIEFNEzSPOx0oIHpuff20Wlu337wSkgIa5jm0ff2XBiJYYCGENvpK5shSTdgoME2wY8EJ47ll97SOWefvau++8c+R5ZkyZbkxFbkU2vtdZblXbtqV/329/6+ImZhEwFJyM/+y73evJXpPxHgbTaSa5zIHAAeRARECDAUgSXEgpRLM1kogWgQHgEPoIaIKKVyJDuNwVODQ+Gj1971xZ+JZBSZdbNprzj7wCcEWnn6yVzVQKH4nZqqxK1BECG0Ds5JjD3Gr06WFoC85F+MxD/D8yMJrRR8X0Os5PuHgntX3fnIP842EM4+ALa1aG5ptwe3b3t0QVP1B4+fHigCMABJnvW+IjEVuuS7wHH2QkQEgPU9Y0QkDMPi6qs3PXoYyHC2gFDNJvBlMhnFLe322X/+2JVa8/2neoYsSI+kIkERwLnSJYATUAQUnLnIcS6AFJneNc7zgNFjioBuzNxiwkySNMUwCqvTvqe0+SgJ2bVr9uzbrKKA0pEx3JiNDmzf9omGuuTf9vTlI5KmTOo8QyS8Mtk78zuyBaEMA6Ako0F8BXicFqVkwY7qJwAShtBqnI0okUEnQL4oozi07ykERXvKFoauvvYPvjpQlnNf6XtmZhX/3QUHAIrYHEYu3qJh8AHHuiP89sVQjCY9TRgNGE2QEJEYHFcvMKxKMAahADCEOZKDOlmAGDV5EErMX+w11TGAS883Cjh0PETPoBOjY9hZJ4gsEFpBMYJUJ8nXLPPPgJNgMbSuOu3PGwRvBLAT7S0KaLcVAM4g5YOk2/v4Aw0i0fVBEBECBcY6RhgBjzw2gN8eC5nwOHJzwZgVwjrgr945BysXeSgUY74oKYPE9pNIffsopNYHrEwagOIRfQ++GrIwARRjRcM3xPd+msPu/QFrSkA/o4DEYAtCwf131+K2VycxmBeomFo639dkoXgLgJ2Yu3pWcK9ZA8D29i0KgE140aqkNnMKQRQjUoC0T+x9PsQLXRGaatRoFjuiWTeOQiwAPELSBpLWUwbgeEKOb4i0T6R8njUXpQBF4CcHA9x6XfJMf5LWOsLhBgBoP7VfKgCcQW1umSJYrE6mDYIgsgAMBNAaOHI6QmgBB0wIwIn+DsGw1jLxTeP1mdDqMuHjxAFaAcd7LAYKDr5hWVVnMXSg4oqOjozZuDEblURHqWjBM6BtOMNUVxJjpHMBTvTaV4oRHVoR/XmH/pzAqBIAhYwiCxFpXoqhppLYUTHDzBwExiyJkKVO5AznY8w1e4cc1CuEXigVa+P9eQdV0ntI0DoRz+h0GAUL4ztbWQHgDGmtraulREEW2liYK1s2YC0wWCgB8BViG4scMJg/a84u4WsoJwtiwXd/BYAzZc+y2awrebEabexyG/ayRU6QL8b/+UphWs4BudKchyctIlorAGoeAOyaBZqwmiXBBwCAF55+IAmy1jkZ1mZJILJAMbz0Lt+pkEABYlPQWNMiCYE0jpZ7KwC81BCMf/qRApCOgw7i8BYCsE4QWgFfYY6fYiTj82fBnNkiOqnZIf/Fwng+zKVEJOlGaoeM7Xvj2vhmsn9UYuM5xooNAlChugLAmQTA4Z1TCZJG5IyXmyg7+WV4Y18pLRpjJCyLgwKkY88jKoboGSW4a99TIoaIwVYmhE4ktgnzAj5TzfiailSgL4zkWgc5e9YCCPzZsmezA4CtALKA9pxWQpaAx5FKyrRttgSYd2BfWCJLMnkA+hemdouM88kIQEVTAeBMlJ1CTRgZxWeH2dZ0gKAIBg7BjfWwjR4kMfVoGKkq+Y+nYQQfb86lAFpVAeBM1IU9KxCOK9RPSwEhgKJDuHYOwhsbMB5DPB8ImYsm9AlPP4BTpALAmSgDRuLUGdeBlCKPz+R+XAALRm6avuQLkAOVGh/yAtgKAGegGqwcQyGsUtROZHjrlGLsU5VpKiLq0gSPazXOoCQoKFbMMDPQDBOoqAggHOm+EomjkI3ihSUhyDSvC2i+4VlTYBwYkwcqnpCZZIgWAGhIpPIKCEpxCMNyv9aEZy4gfIkjzDBTvabr1yGQKOWhcKxIIDJYYcEzMLdKFZl3QN6QdWV6IQJ4Kk4EctOlSKGAdnqahPhq6lS3BLq0P37WkQP7KgCcSfArbfCCt1TnD+3oHlCKC0oxqSxnw6USMRinZA2xAqnxkP6/n0di+3FIjTf5kHwAYojB/30V3DwfKMqUYwKrkgpjvTriBBroAiqekBmWkwSSWXdox9ZurQnGCnCJBQM1KTU9CkiAQxHU6SKkKFPPCZnGoALAaKA6OZpqC0nrBI48BQAbZkFeyOyJiG5vUaVdOqFL9ovybmoCdekSADlNU4o3zWuasYAJw/ijcaNcOqoYWmjBCQBor1DAGdTKwZmUo0pxuMhKWaBvrFFnC/TT1YCn0mca4oR1QFVCoTpJWCfliBhRSrFYtKH2eQIA9u1bXaGAM44XOzzHMRsqDphbq8/YAjHzo2DmVCmkS3nD5ex6oxUE0uXXzDkZa//ZCgAxw5KStMbBaExOSOSAeXUaCe8CNOGLqM9bC8ytU/BHaO4knWcUSLyw6IZsbraU5phFFDBmR1bpQ0P5UAjo8o5GTtBYo1CbUjM/MJUxlV7UYOKKCCPyQYxREMFBANi1K6NRMUTPpBazo+pI/845d9IzClLKTLIWqE0pzKtTiKzM7MD8UiL9kiYN584oTVJyKZL41WzxgswqAJIQyWTUwk2fHSL4jO8bkHRld5xvgKXzDCI3s2uCWQdUJxUWNxqEdtRUVTG0UIJfAABmSWmO2aWEbCi9j8JPPa3KBR6HKcjVC7wZnZxOxhWyFtZrNNWWqHXMkkVrpYbyYa7g9K8BoHUWaMCzrzzbhjWx8dnyyci6PxtWRBhnmC1fYFCbUihGMiPlwBiAwIqFBimPGChVxiLhkr7RQ/lw/+rND3aWje4VCoiZFpSwTwAgFP7rYK6Y04paBFIuzzavTuPKuRpBJDOzSoLEhYnWLPFHGc1FRHxPC4kfAQBmiQIy6wCYzWadZDJq9eYHOwXYk0p4IDFKDnz1Uh/Wzjw5kIip37xajRULDYJwFJVWYWSpwB2zSf6blYboshyoiMc874wcGLNh4PqlfuxjnWEMjKWCRNdd4aG+WiEqKSBxeV6tBnPhqSDtPwUAaGl3FQDOXAA6ALCU7w0MFS1JPQzAUHBFk8E1pQqoM4kNS4n9vmFlYhT7JcSmkp4AsvPamz89IG0tejYYoGctAMmsy2QyauVtD++PrP1ZOuXFZSvLm6yBm65NTD8w4WVSPoJQsGy+wbWLR38cQtI5oQDfnC0FiWY3BQTQWmbDgv/HN5plNqxUXH1+7fIEljTpGVOwSJWUpPWrk0j7I8UDcQlP6/6h4IVkn3kCADZszNoKAGc8G261iD0gbX2DhT5jtC4dRoTIArVpYuN1SQThpWfDJBBEwMIGjXWrEnEZOTXMll065QHkP16x5fP5jo6MIWYP+521ACQpIm165Z0Pn3Ii36xJ+wTEDlPBQLB+TRILGzSC6NJSQcW4DNvtr06ivlqN9H6IUtQDg0HgxP1XANiwC2627dXspIAAgH0CgA7qocFcMVKKCojT1kML1Fcp3PXaFIJLqIzEsh9wRZPGra9KIRfI8AE2ImJrqxOMrP3Wqk2PPCdtLZrZbAWAryRlRNpa1DVveeg3xTD6Vm1VQonEVFArYCgQbHxVEiuaDfLF4bM4LjL1I4qR4A/fkEZtmrF9cjgnhCqXDy2h/kYAts/SfZrFFBBAy2oRAUXpv8wVorBMBYE4VSPhEe+8uWpUjcuL1TTjutVrr/Jxy+okhgpnPgIRiWqrk6pYtN+4etMX9qKtRW3Z0m4rAHwFUkG0x1SwEIZ/X1eTHKaCikCuIHjNMh+3/14KA3k56/y2l7sIeXVS4V1vqh6deFQOPMgFeY/yFyIgWlYLKhTwFWqS2bdaMpmMomWmfzDo8j2t4iD92PuQKwrecXMVls2/eKyYisgFDu+8pQpXztNxLWgOI9DWVSdVGNlPL930yHNA26w7pPqyAmA2m3Wta9Zw5Z0Pn4oi94mqlK9G1qu0Dkj5xH1vqYGnMTYG72U5A6Q/57DxuhTecn1yFOUVEZdKeaa3L3cwUeP9jUhGAVvcbN6fWQ9AAOCWLVbaWvTKOx7+as9AYUddddK4kaw4EKxaZPC+W2teVh9x2eNx7WIP77u1Og44GMF9laIjCefcvVes+3we7fs5m9xuly0AY6tMrJDAmQ/kg7An4WlKiRVrBQzkBevXJLBsvkEhfHniBYnY43HX2hRqU0Q4wgbpnNj62pQZygefWbH5i7s6OjKGs1TxuCwByGyskKy443Mv5Irhf0wmPKVAN5I6RRYvu02wFOEcF03lcA1rW1udMD39+X9d4Tf+ubS16A0bsvZy2JfLhwIC4JZ2Kx0Zc+0dX/wffQOFT9fXpYwIwrE1Zi7mUfUi4hKeUUEYdRUjvoMbsxFaVstsZ72XJQABABuytqMjY1be8fAnenrzP6ivTXrOSTQptEwXZZiwoI1orURrSD5ffPu1mx/6XRxulXWXy3aYyw1/JESk1WYyUHn/1Ds4FPyoribxmv6BIJqo+jyLbupAVATC0oHAHDf+TxRpq9O+6e7Nf2DVnY/+s3RkDONzgC+bdvlRwFKwQmsrcN3GRwcLIe8qBNGh6irfyFhKyNhlEi1Nx0CKZHJCoiY4EMLNT0BqvbOOdijlqdi62qTp7c//+ao7H/nK5Qi+yxaAZS9JW1uLXr35wc6+XLCpGNkjVWNBqAjmLAp3zsfgAyvigzvyduLKpyquhs7eEOHaORj4i2tLxzSMTDCKwVdfmzQ9/flPrbzjkb+5XMGHmZ2ifXGatLVobmm3v35s61V1KbPD9/Ty/sEgUiPZsYsLVZrf9KPq0edgDg5CakwMuDKLVYzBCSD/h83IvXNxiX3L8GcuIkJFN6c6qfv6C3951aYvZDo6MmbjZQq+CgDHgvB/fnBJbV3iB+mk96regSAk4WFktdS0BvMWqf/+IpKPHQcDB6nSYChAwSJaUY3ce69AuLYeHIxGnSviRJxWZHXa50Au/MTVtz/06RL4LHB5aLwVAE4ChHvb3t9Q01TdXl2VvLW7NxcB0CxXPXdxtUtJG5hnBpD69jF4e3rgGnwU7lyA4C3zICkdg28Em3YiNukbTYUolwv/4zWbH/n65U75KgAc1yySUWTWdXRkzFLX+6XqdOID/YMBnHPD2XWQEktOa4CEeXYIrt6Dm5sAh6LYwqyGzzMSiNjamoQphq6zUAjvWXHHwx2Xs8xXAeB5WiaTUa2tWSEhh3du+5Dv6c9qrZJDQ8UIpGb51OtSDJUkNRgJELpRVE9ELElVX5vkYK7YMZgrvm/N3Y8eqVC+CgAnd0ple4vilnZ78Icffm0y6X0plfJf3z8YwFoXASOAKKNXUkQcAKmpSugwtGFo5a+W3/bgpwC4MpuvrHDFDHNeYzW3tNuOjoxZsfmLP3/sQO7moaHgPxut+ubUpoxWpIhEAlihOIE4iEROxKWTnqqrTuqgaHcN5e1Ny297MCsiIpmMqoCvQgGnLRcCwG+//8HlqXTy407kXdVVfnUUOYSRg1KE7ylEkSCM7M+tc59Z9uaHvgEAFZZbAeBLsk4ibYrcYgHgd9s/skz53r93Ihudk2UEBrXiL6j4nb/vqH08m826+LDpDC8nv26lXQQFRdpa9JiAAo5n0qmsVqW9rEDs6MiYOGQ+Pn6koyNjSsCrcJVKq4gxlVZplVZplVZplVZplVZplVZplVZplVZplVZplVZplVZplQaApZSaSVvzWwFkMbpWcQZQrVMbVyYqth3PJ0NgP4GTo+a1C8AGzDur3y6c5Iaz/gZswAYHZGUyhb3L4+7CLjX+syY3LjBP4rOLzz9uPGaLGu89Mc6Yu0r3jT9muxDj15AWtOixY4zXdgHYiN1RnEbVMrz+5fcf/b7zBGh35Xcc+y4j1+xc/TCzjkp7eZz4ghYtE3xkAvDlHHe8v2cA9XKMKQDbLvC5MkXXYry2Ux+z3IenF67bWqP0lgGxDucJUPWoEDrXG7rBdyw88ashADi8fG1dXT7xTY+qOjx/EXfbSKO7JPpK07Gnvi5o0cToIM0OrDc3LJZrRewKcVwcwc1VZK2DVAFMUGAEos+8CB2JkECBQA4ifQrqNBVfVHCHjqVqnll56PHgfBN7fvGNqQbrXSt0V0fkIifSBEgtBGmQvgg8QtQZBzCtlMYVSE4Je0mcUqKO+iIHE8d//Mx4FKlUk0gAoH/h+iYgvFYUl4njQkdpgKBGgBQpvhMYlgAhgICwFBRJFCBqEEQPxZ0w4BEt7kD6+NNHygDPAk6QUUTWnW6+6Y/raNb0udBh+BCI0YwwpciCsycaO5/6u+4Fb7zS0FwPyCqhWxyB9RDxSUYUdivK77SoX4uLflFz4umTANDX/OZGxcKrrGANhEsdpMlB0gSoyAKAHgU8r8Bf9kv+6UWde3IZQBmCq3yam9MA9DnALwB8Et2QfKLoDefMJvPwANxWTW1CqHN+PhEEUAZ0UYnLxOS6xMKlu3ndAwnae0OHldVKU2sC0KMi3wWAjYPt4lPEyeGvZuTYFoIhIRbmBg/3LbzpH2vrm/8v7G8PS/eJAGwF2Lq6xfT2df4fxuFdVsnSNE08IkeXjnYA3Ihxz8Tkjx43gmDIORc13/LMaXH/tanzyQdLaUouU/rtXnjTFT751452k4ZuTFBB6dFrjdJ7ljM7JxpToBGKoADmhppv+emgRH89v/Pp7TEb3V/Ojnq3Md6GOsq4eywAFIg8nTu98KZNinydR9T41CD0qK+ovNZFERSpe04vvGl7PJ1gA8D5aSpodXa2Akf0q2fVc6ebb/o/m449+VVDMF+UyObE2uHdngCDHkhS+hy1nBHmlFDQNyDRnAhyvgOwoqTQiDAYSYqJdnv/wpv+U4P2/3rQhbAQ9LlognxZ6mpqhhAYEP0ugkCicc6hJkCtyKtqdSLT3fvi4kbgAzGLardAi8qi3W7tOfZgo0l8sN8VEYpIn4Ru5KN4ZoNMihq2NG6fi1y5vuDZEf3UQlndqP3Pn25eV8tjT/2lYL0Bdts/mX97lWNue5XyVvW6IooQVxA7skx0uSIIEkoZAw6DcMBF0QTnbSsFpj2l1teKWX9ywY0bePxfdu9dvc/HflgQvaErRv3xmuqJzqpTpGkwiVshDpE49LhIALHE2R+HAMqDqq/T5h0sES8LgRMZ7ocR1H5kvxT1sjnKfOXUgnVFJRBFUJcqmkx4ofQr47yAlPriHP1HjlEG6R4MEmh3bbGM9v68i2wgLoq/GGqCpnwB1BrUBhgaEPuRSOT2HOx7FHDKg9Iy5v64P1AUsb02sCJ89/F5b5i/Be02Zk3ttufK9XNI3NNvizYUZ1kCz8jnCKj9mFMcyzt7T0Hk9pzYj2igoM+886hxASAQFw250FJ434Gr70i0YrcjIL4q3DxHmVVdLijaWBlTGN3fCKCqlDZW5EcFcb+fd3ZT3rmvpaiNgGrMeIagEkD6XRQkqGCUuhcA/OIVZVKk4zWEGaevIWgUqTUQddvCV7pd+PE+F31GAwMGykj8nmbkPBWoIoj0uzAadFHQbcOv9bjwE/1xv34DZWJ2f3a/gtioKM6R+PglrY61di3APRBZ+GyiG4mqCKJjxXz8bzRJo4bEHph77Mkvlv/a1XzTPdVUb+mTyKK0+WPIoBKAIJRRaABwYhd2KQBOilGtQBKOONe4Lq207nXhT5s6n/5/S398oqt53YdS1Ktz4tz4VJ86ElAg6XSuqzoLdMXSlp0rUCXgTcgtXIpKDbnov83tfPqfAKBn/usPhvTex4nldAIwUZyW1wgARf95maTi4ZJUKhB3tPHYUx8YXtuF61bVanN3SXYcj3JKgtoUxB1t6nzyj0f0W16nzR/1udDGADx7bQIRElhySQE4ZhEiQKJy/Z7xNiWm1rAdWG82YJ7ahZOOEirhZG0/Ss76t9jJzA0Qmg6sN3MxT60BbDde5GQjVavVGZEFhHASmqbEV6qsLfZIZ41MwnLBM1LD1KNqBdEB3JFYgecFmOu6EbnJ9hO0+MA+TKYfzwgr0zsZIxcpI1hvBOtNEKkLB7ELSWBujfJMvTJeg/LM2GuOMn5K+QZAU2xfGuAGzJOLaEySjdgd7QdsSXMXAVxJ0z3rGvF3mX7OLB3Rbol2K7QXI7mJLyJvgf0RsTuaIn6n0286BSopV/T/S3f5X20ncfrWheumt8h7quN+J7yiLJRPDrioOnIiDhLbCqjoIKpkt3ZpiqXgSAkAFgC6edOlyjrzE1QqwvhHiwgAD0QEl6j4O14CABKgFQFEarsWrvu6kMXSUichqHIQcJr5EcSeEJ34wmTu7V18Y0PfolvuorjXOPC1AnnDkDgZ3771srajRedSoTg3gVwmLq463S86UUnNfCkooIvtbslq6vdwxJc+CHvB54juXb3aX7O/JSLiPFrBWq9vSeIKY9W1EfBaQF4rwHXWYWk1qY0yiESQE4sS+C9Kayn99nve5gYb8PQ57l0CADohOLI76MB6s3GK7KkCwAla+BK78QQg9+8vPrV4e2pIbrnTOrmzj3i9RHKVUSqVJmEBFMUhEIcBZ0MhTIqKBCEXEYDltvTI7mAYZOfnHtJRwdqFA5AxFQzzYn9CMColZnsgXq9i+9U0wBe7i7qa170xKfrrPrmSWiEQhyIEgxI5xEdrUQAaKFWrlDcoNheIfUaAJR7U3BAivIgpkryMi0peEgAKIB7JokhP47FgI7EnBIAXF65NJyRxVJP1UwXBHgxyLbIiyKguPPHlNPXK0y4MS5YKVfIqKMS2PDGxGb9/SNyfJmh2Vr24++jp5nU/TFPd0SfRRLaql7S1n7E/fi5JtSjvnGB8sxE8KESQXBSZrfNO7R6qwO0lYcHC3rqoSvrQDwCdYqvA6VGeM4bo76coibn9EjrG1npObIh2B5uO/fhrI+LJPOElqVq0Ja3NIo8OE2nBBkSXK0rSy/0ZgcEK3F4iGdDqRNnOhaPKcy8NM6JVoIrNa+difUJBi96DZ9UNMRW+JKxQiJ68C+fnRRxGRMmMNFcZgBD0idYVdo0ZXx9w8nSMaLdrsfySmjYIaMRyryn7O0deZ/4OfTHWpALAi7f1Lg41GjCCFo2Ld6aaCFr09Rgwgoy6GJRXUdmyx4kilAoLfplaM0J0MohjBiYO6YrNLZKO2X8cZNol6/wLoRM8H88vIY1k4owH5vFJjSvlH3WWgcBNUvFLlV1bfebmoGQCO6eiJ68w7fzSAnBPtQgyinuy4enmdUcS4JUBJALojV1kgiovTjSwqqv5pu8I5BcUziPw+pzYKXlCSj5kvqDC01VO9SSoFuTFhTHbBEePTTXorCjBm7qa1/09hEcFcq0ilxfEyVgvSAkAAiBKkL4Vdv3ieT1QNjc5pQ45ESWAi2PmSl7H0WPqAWdByCdONd90hRL0RHBv8qlBOesDLX1AIhCEnlZJFfF3ALCmeAWB/TMbgAK6UkCnPRcxIFiOUhkvfMSWniHnklsIRKUY3xEUII7aFZEHleL6Gho/5ywiQAhxZQpVCvFgBLJO6X9nqP8doDDgAgTibKw5nx0gyjIBG/Vy7QK0qCuOtue7Ft7c6iv1XxJUfkEcQhHYGEPDgQQuDof3a2jer1R89NuQRJajjiIkGcd705BMUvkCARU+tRG7ow4gJoMv/vinp5vXfaNJJ95ZFItAHCKReIx4ilKmdAqcW0e9lQoIRFAQG5Ud//F6UBGgB8KjYkrp5KCLTlu4hwQg6k650tScxIGldjwCSdDFY49ZP2Ja/UqYsoxxwYn2RCDOKEiVr3xTLTTnC8k3JLps2KBGBMlSHEE21ikP0Xk8EhHEKOWBrpAeqVAIQHY+/Z3O5je+tRbmYwRuSFNV+6QeGeTvAISxJyTQcC8UxT1FYGOT9pcUxE5oDWKp75ArqJHjZgDV2PnjL5+af9OBlFbvj+heL8BiD0z7VEqD4IgweCcSn1UDoF55WkpigZM4BSAQgYMMRoKjgdifDLnoq/OO/8vuOA9kd1QGa9Oxp+7pbV63w0BtcZBXCTA/QeV5YGz0LI1ZTj8QAXwQKeUZiT9W2FL4fyBOLKSHgmdzLurocsUvLT3xk+cEIPYsd8AeEJL2aHSSosfbYwfoFBUCFKvHrNuk+hXO6idpQ6MTE/QrRfpgQKIanlrwxtfVa+/afoTnPArSAUgCyIkEc48F3y4bog9cfXViztDcP0oo5YXn0WosnDTBYw/cLxte/PGvRibolBNpAGBo8Y2LaM3SQGS+KNRQYECxpBrSkFOG5mgymXqBhx4Puhfd9Hv19BZ02aLwPFpj0VX/eOGJnUMyOlRclU1KgvUmtziYX3ScZ8g54XCCkPIpME6cLn3hAopVgtApFRAu5zkMRNr0+kpOVz2/4GQ52Wrk88f9sBfene7zehfAsQnW1QlY5YCUUHwAmhKbeIR0ACyFRQUpOKicoe2nSI8wOlV37KddYxOfyr8nF9742nqdnNt3jjVKaIOitbn6zqd+XKZSPc1vfE21Ssybar8Tzeuub1D+/HP10zAQSjTj0jKnkhb4UqU2Tje18HzPPFeKZDxmRr20Y6438gqzbDCe8PpJT3oX4uRljEml3DClYXe7c1GFOEuuhWMTv3cNJzu3Szm5Pd7E/Zyk/fCcAaLDmXLIDMum4yefT5S0HiekT8VXXC4M0I4Wtpwz4X2ipPUza3Euf/sU1she1H4yRmzjBHa1kfdxdNZdpVVapVXaK7Px+ccfaDjafzS/ePFiSHcheeXdX+oZe9Petha/efny1BO7ny22rF/NZ3s6vatu/3LfBZ/HxkpYE2ZceZTYtzQRJ3yp91uF2n2muWnRQROpg4Hx7isfT1XulMlkVE26qaqnJ9+2bu3iAy8M9P8GNnkLALRN8UCWtrYWLdKmh89jA0SkdObGNGP5ROLDY+QlikkVyai2thY99pK2Fi0jzgbBNA+5yWSm3r88J5mgrwgo5/j/yYCjfO4JASmDT9padEdHxkz/uRk14X6XD/g5tP3+baee/ricfOrjcvjxD98+9qSfjo6MAYADP9z6D4M//3M5uH1r0Pnkx+aVF3Uqkxn17wNbE5M5dei8X9VLeGbHZD+CqYJw7DpNad3GzKm8H5Mda6pzE8koObD1ghOpxoJW9mb88dbNOIguhpETASKhLyLErlaWwbBnz5cpmYw6xG4pFCMHIIiKRX9qQBGSdM/ueGC99uTdzuF1zx5xc1nfnHv+/3tgvwO++7XdP/8HkpEIeD7yXz5A8NAT99/4wi71nxWVyRWKv7x6UUMGa1pDcmp++/LzDvzwI29+Me1/NBdEiO1vLDnj4LRWPYrqmaBQ+DaZ3TfyEMNzfSAk5L0bTs374zf96aeNpxqLoe3OF/s+ngU6z/Wu5ecf3rHt1qMJ87EocnDODUnU+QGRzEBrK9Da2ip79txn6k4n/qKmOvG6Yhj1Rm7wk1ngSGnNZTL70vG19ySXL218H8Td/dwTvdcIWPXsE/d3aeKXhUh2+uRP/EL+yKLf/3JuKvu9/7GtN1al9b1iceNzx3sacRy5I/98/z6l1HeP9RS//fo/fKRblf2dAJWhFEkKN2YjkkJSbrjhvpDZrAPh4uhkUuzko+/jhaQc2rH1c8mk2jWvoer9vqdf7azUCnBVY336rXXV/t+/95brdx1+Ytv8yX3FsalDQrcvKEbrF86rvgPEIK/LFrGrdRr2vFYBgETa7AtCu3lOTWJzVTqxqSrtb6pK+5uq04nNc+ur/kN9XfIvU+nkngOPb/0gmXXno4QkRNpa9LKNjx4vWregeeGczdZK8+rND3a2tbXoc39o8Zy05+8LitHmqrS/OZX0/r21ydvIrHtrc6fGrlZ9ww1fDqGkd/6C2k2Fol2x/M2fPZLJxGt+PgpFUn63/SPLll9Z/1Rdtf9oU336TgGucg7VBNbMbay+Z8n8mq9buO3FmpQ/ntVkPDGLpBzavu0ddVXeU/Prq98XRnaVtXDOoaEqnbhrXlP1l5sb/WcO7bi/VY30aDuw4ZnvfbTp8He3zX+m46NNz3R8tGnv9z+04JnvfbQJglTsB58CZWlr0WTWHdq+7RNN9VUPOCfoPDn4j4XB8PcSMFcUIyw70TX0yZ7+Qr6hLnWTtfLN9vaWSRe7rEtZJ4Ke/qGCFTJ3oWwjYbR1VroA2KGg+MmBgeDq/GC4KjdUXN15qu9tJ7sG/00rJpIJ8+ihHR++gcy6ycrBBPtyg4ElMCXlLaE966zrHRgKbKEY2VRKf/PA49vedsN9Xw6fPtXvlbwkudxAwZLsnazo0grgxe/dmw7B79bVJF/T3ZfvOd41uLUYYVmo7FJau7zz1MA9A0PBs+LwD8s2PtTb0ZE550cjAFta2t3etowPyF8lfMNjJwc+kVJubtDXeaWLZEnPUHHtiycGPucs6pTC901cWkkhXyhaKvUPOhFZR0AXY1uz9g0gEQh6A0NFkKIn+5Jkuz288946cfgz65wNgnD7VZsefveI27oB/N3Bx7fmB3LFh6rT/obrZeGtzGZ3TvZ0cZaLKsmFewBy+ZAC0UYpLU46V9758OER//2bA49t/Ume0S/n1CQbT/fa+wD8bO7c1ZMtDKJJjFvc6dxzKpJURkRorUSe0X4yqb95YPvWd67c9PlviWTUoR3diqSGTO7Zu3ZldDabjd69/f53N9QlX9U3UCiGTt51zVu+8NiI27oAPPfzx7burE+pEADOe+5xvOmy/9unawDdlAtCS+KgpyVYM3e148ZsP4CfA/j5gce2fmXlnQ/vf9nCsdrbWxTQbp1NrPE8NTcoWkTkF0WE+9pbvTUt2RDtLQoA9vXbr4H43+Y2VM3L54u3ANiJSW/sy2KKgFL0JZNR+9bArNmHaF8LzMrrskcPbt+62/P0HwGyBgA2bMi+zKegDwHwoRRFxL23EESfqqlKXAUn3/jt9m2GzH7z0I5tU9rHDaf2SylIZpPvKxf02l9cc8fDj/3sZ/d6a9cutAd3dt/ieYnfJnRgk0G6eLxn0Bx8/KNLjiZqOs8FQpIimYzCH6Ln0I7u39akE6/rHSj8z4Gi6Rpgz+lnd27ro+Ipz+i9ff3RV4Yjop1zSPhGi3PvsYG5UuWx3PrmSuubK4NidJUNzJUi8j9qqnyI0E4lgVsT1cYoKRYtjHOn0drK/dhvSQi2tDtuaXdrcCpPoFsrwoF1M+SodGE2607NhWM2606dgpO2Fk2wu1Q+Lnkuz9FLHP/vfM9oS/OvRtzt+SA85nnGpBP6vx1+YtvtFu6knkqZn32ry2FmdSQVyRdFMqr2ZEKRWUfBxxtqTGchUCe7JN81Z27yd2T06UX5bn1eC0ArQGYd6T40kAsOeEahYU6qcX5j1TXzm2peP6+h+q6aKv+TNVVq/8Gd97/djHSvKUj3it//3LjJ/ge3b82TUyBKLfFLinKdQTGSmnQCvaG9jtnsT57reE9S2lqwD6s1tmSLz8yZN98nFxcjRwAnprVHpJKOjPkdYKQjU/LRAtgVA2iqz3MiWjoyZlfpeXsOdJL3tUcHtm+92jkRAr0jtdWXG4POOcBGTUvveOQnv/7+B29DCturUt6SQhB+S1E9OTAUAJiceLRrAxSycBAcd06cQK4hs046MlY6MuZQsfvXhSA64JzLC/jahtrUHfkg/NXKTQ8HEpuB3MT7EJ8WT37xZwCueaHjYxv6BgpLRTBXIPMILHUit6SS3nyE4UNmZLjMCDOMxoZWWzLDmLVr740O79imR1S+O39pMmadiHDXrtbfLC5271OarzJG/affPvHA9mUbP/8iyhFaABI0f5tMmuqBwQDOuR+UvO3n3dTuvgK9VBVIwgGDjNnDWSyioyNjziu/AFCFiM7TcWgp0T/2ec/uuP/3leYbI+tIJT8qRQeoyYTYu5L2OFVbJwshJeWXsmEYZjIZ9aq7s7/Z/4MP3wZiZ01V8op8IdxcLFpw3Oy8cVjwhjWlgAl+qxBE/yGZMNc+u/P+j3Nj9tOlW/68fO+Bx//0noSvbnNWCpN1NsSy/7ablePgko2f3TX2nsM7t37Q9/TDuXzYaAQsxBHNgBZXICnS1iJlNb6jIyMk5dAPtwblyOeg6BcnJwduUVu2tEeHdmx7IJcPn6irSa7o7S88eWj7tkeFfEYgjZp4Vzrl3ZpKehjMDX3mmjse+bf4Jc4vWyXrbBgW4QpBaOncmw9s30aKaKVp4YTKM+Iie43Nd38awNHz2cbyCYaegysUQ0un7jq8fVujE9GK8IR4DYi319Ukve6+3HGQX4pNEq0WyE6GQhdBWIDFqQAwn0CYgEQC2MgyzGazbu/ejL/6uuyBff90321EegfJRQJRbpLPJrfYmJW2fufAjm3fb55bc3dvf/7vDu/ctg6QfwLkBMA5AK8H3NuDojMgN8nezCPYv99ORgE9tFM+k0p7rzm88/6vUtxT1roX4CkqYDWEH076RpN8yhBYkU75WpE4GYTLzhZY18jethYfisuSCaOTvpkTFOxiACdbce6l37Kl3ZZY1D8/84OP3Anic7XViVVVKe9vI+uglYK1Dn0DhZ5cvvj5lZu+8KnJsLTW1jhg2EV18zSxEELdVJ9+WzJh3laOwnQO8DyNk12DGCzgU+eWW1oJQAzV/IRvGgiiqSH97oSv3y0lV0TkBKd7cjI4FPwvcfjQ1Zu+cEIyGcUs3flEkQOPbU0oYklp0ZcceGxrYsXmhvDcU4rn5Cl/vqd1Q21VAkFhaDGAvWvWIOroyJg1G7MH9333Q3dX1fj/VlOV0EEhav7Z9+5Nr31raz6bPd9HkRWgFXn47+jqHnpYad4zv7H6D0j+gXMOSsXR4CdOD7rO0wNPUPA1FDoFLe3uPAZoe3TnhxtFeKQQRCvmN1b9Cck/KYYxI0n4BvlChJPdQz+KxL3XKCUHuntzH00lDGHjagfYEg8S8/It9vnHH6hznvunzlNDP6hOe6oQBjXlQ2smw4rb2lr0qrse+eHetg/9Lz2Xbx3KhW9wIvO0wqBS3FsIgsdW3PHoobIF/fyH5WSQRRYK0phKJz7ZP1R08eufyU2gUzSGEkZ2tfa91PkO3wEAz6HWT+qPDeYCN5grDj/Po3Yg+o2nDyx502f/tWwsP59sGa9f1h1+Ytsc36hvHHmx978nDCXybD2ZPT4Zrw9h6nxPfSyXL4Iss+9W2bCRVjIZ9Wy6cBQuuL+nJ+d5CY16JptIPn8+ak/GeLl+E4YA/PGRjj99tKsvf7u1bgUgSYKntda/IsxTS9/82f2TlMMFABbd9sVuEm/f+/0PLejtL9wSWnuDCBYDgNZ8AcSTy2/7wvdJyP8PHthrKSnJ9hgAAAAASUVORK5CYII=">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    :root {
      --bg: #f8fafc;
      --surface: #ffffff;
      --text: #1e293b;
      --muted: #64748b;
      --line: #efd9dc;
      --soft: #fff5f5;

      /* Chuẩn thương hiệu HACOM Holdings: Đỏ chủ đạo + Vàng cam điểm nhấn */
      --nav-gradient: linear-gradient(180deg, #7A0C11 0%, #D32F2F 55%, #FF4D55 100%);
      --primary: #e1262f;
      --primary-dark: #c61d25;
      --primary-strong: #a9151d;
      --primary-soft: #fff1f1;

      --accent: #f6a623;
      --accent-dark: #dc8f12;
      --accent-soft: #fff7e8;

      --warning: #c47a0a;
      --warning-soft: #fff7e6;

      --danger: #b71c1c;
      --danger-soft: #fff1f1;

      --success: #24a35a;
      --success-soft: #edf9f1;

      --shadow: 0 10px 28px rgba(177, 23, 30, 0.08);
      --shadow-strong: 0 18px 42px rgba(177, 23, 30, 0.15);
      --radius: 12px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }

    body {
      min-width: 320px;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      font-size: 14px;
      line-height: 1.6;
    }

    .app-shell {
      width: 100%;
      min-height: 100vh;
      display: grid;
      grid-template-columns: 250px minmax(0, 1fr);
      align-items: stretch;
    }

    /* SIDEBAR CHUẨN HACOM */
    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      background: var(--nav-gradient);
      color: #fff;
      padding: 24px 16px;
      display: flex;
      flex-direction: column;
      box-shadow: 6px 0 25px rgba(122, 12, 17, 0.2);
    }

    .brand {
      display: flex;
      gap: 12px;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid rgba(255,255,255,0.18);
    }

    .brand-mark {
      width: 48px;
      height: 48px;
      flex: 0 0 48px;
      padding: 4px;
      border-radius: 12px;
      background: #ffffff;
      border: 1px solid #FFCDD2;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      display: grid;
      place-items: center;
    }

    .brand-mark img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }

    .brand strong {
      display: block;
      font-size: 13px;
      font-weight: 700;
      line-height: 1.3;
      color: #ffffff;
    }

    .brand span {
      display: block;
      color: rgba(255,255,255,0.75);
      font-size: 11px;
      margin-top: 2px;
    }

    .main-nav {
      display: grid;
      gap: 8px;
      margin-top: 24px;
    }

    .nav-item {
      width: 100%;
      border: 0;
      background: transparent;
      color: rgba(255,255,255,0.8);
      display: grid;
      grid-template-columns: 32px minmax(0, 1fr);
      gap: 10px;
      align-items: center;
      text-align: left;
      padding: 12px 10px;
      border-radius: 8px;
      cursor: pointer;
      transition: all .25s ease;
      position: relative;
    }

    .nav-item:hover {
      background: rgba(255,255,255,0.12);
      color: #fff;
    }

    .nav-item.active {
      background: rgba(255, 255, 255, 0.18);
      color: #fff;
      font-weight: 600;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }

    .nav-item.active::before {
      content: '';
      position: absolute;
      left: 0;
      top: 15%;
      height: 70%;
      width: 4px;
      background: var(--accent);
      border-radius: 2px;
    }

    .nav-icon {
      width: 32px;
      height: 32px;
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: rgba(255,255,255,0.08);
      color: #ffffff;
    }

    .nav-item b { display: block; font-size: 13px; }
    .nav-item small { display: block; font-size: 10px; color: rgba(255,255,255,0.7); margin-top: 1px; }

    .sidebar-note {
      margin-top: auto;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(246, 166, 35, 0.3);
      padding: 12px;
      border-radius: 10px;
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 0 3px rgba(36, 163, 90, 0.3);
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0% { transform: scale(0.95); opacity: 0.8; }
      50% { transform: scale(1.15); opacity: 1; }
      100% { transform: scale(0.95); opacity: 0.8; }
    }

    /* WORKSPACE & TOPBAR */
    .workspace {
      padding: 24px 32px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #ffffff;
      padding: 16px 24px;
      border-radius: var(--radius);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }

    .eyebrow {
      font-size: 11px;
      font-weight: 800;
      color: var(--primary);
      letter-spacing: 1px;
      text-transform: uppercase;
      margin-bottom: 2px;
    }

    .topbar h1 {
      font-size: 20px;
      font-weight: 700;
      color: #111827;
    }

    .topbar-right {
      display: flex;
      gap: 12px;
      align-items: center;
    }

    .btn-swagger {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--accent-soft);
      color: var(--warning);
      border: 1px solid var(--accent);
      padding: 8px 16px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 600;
      font-size: 12px;
      transition: all 0.2s ease;
    }

    .btn-swagger:hover {
      background: var(--accent);
      color: #ffffff;
    }

    /* CARDS & SURFACES */
    .surface {
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 24px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .surface-title {
      font-size: 16px;
      font-weight: 700;
      color: var(--primary-strong);
      display: flex;
      align-items: center;
      gap: 8px;
      padding-bottom: 12px;
      border-bottom: 2px solid var(--primary-soft);
    }


    /* PROMPT GALLERY STYLES */
    .prompt-gallery-box {
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px 18px;
      margin-bottom: 20px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .prompt-filter-bar {
      display: flex;
      gap: 6px;
      overflow-x: auto;
      padding-bottom: 8px;
      margin-bottom: 12px;
      border-bottom: 1px solid #f1f5f9;
    }
    .prompt-filter-btn {
      background: #f8fafc;
      border: 1px solid var(--line);
      color: var(--muted);
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s;
    }
    .prompt-filter-btn:hover {
      background: var(--primary-soft);
      color: var(--primary);
      border-color: #fca5a5;
    }
    .prompt-filter-btn.active {
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
    }
    .prompt-cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 10px;
      max-height: 280px;
      overflow-y: auto;
      padding-right: 4px;
    }
    .prompt-card-item {
      background: #fdfdfd;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 10px 12px;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 6px;
    }
    .prompt-card-item:hover {
      border-color: var(--primary);
      background: var(--primary-soft);
      transform: translateY(-1px);
      box-shadow: 0 3px 8px rgba(225, 38, 47, 0.08);
    }
    .prompt-card-title {
      font-size: 12.5px;
      font-weight: 600;
      color: #1e293b;
      line-height: 1.4;
    }
    .prompt-card-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
    }
    .prompt-badge {
      background: #fee2e2;
      color: var(--primary);
      padding: 2px 8px;
      border-radius: 10px;
      font-weight: 700;
    }


    /* UPLOAD TAB STYLES */
    .drop-zone {
      border: 2px dashed #fca5a5;
      border-radius: 14px;
      padding: 36px 20px;
      text-align: center;
      background: #fff8f8;
      cursor: pointer;
      transition: all 0.2s ease;
      margin-bottom: 20px;
    }
    .drop-zone:hover, .drop-zone.dragover {
      border-color: var(--primary);
      background: #fee2e2;
      transform: scale(1.01);
    }
    .file-preview-card {
      display: none;
      align-items: center;
      justify-content: space-between;
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px 16px;
      margin-bottom: 20px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .doc-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
      font-size: 13px;
    }
    .doc-table th {
      background: #f8fafc;
      padding: 10px 14px;
      text-align: left;
      font-weight: 700;
      color: #475569;
      border-bottom: 1px solid var(--line);
    }
    .doc-table td {
      padding: 12px 14px;
      border-bottom: 1px solid #f1f5f9;
      color: #1e293b;
    }
    .doc-table tr:hover td {
      background: #fdf2f2;
    }


    /* REPOSITORY BANNER & VIETLEX STYLES */
    .repo-banner {
      background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 60%, #b91c1c 100%);
      color: #ffffff;
      border-radius: 14px;
      padding: 18px 22px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 14px rgba(153, 27, 27, 0.25);
    }
    .repo-banner h2 {
      font-size: 16px;
      font-weight: 800;
      margin: 0 0 4px 0;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .repo-banner p {
      margin: 0;
      font-size: 12px;
      opacity: 0.9;
    }
    .repo-badge {
      background: #fef08a;
      color: #854d0e;
      padding: 4px 12px;
      border-radius: 20px;
      font-weight: 800;
      font-size: 12px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
    }
    .vietlex-box {
      border: 1.5px solid #bfdbfe;
      background: #f8fafc;
      border-radius: 14px;
      padding: 20px;
      margin-top: 24px;
    }
    .vietlex-result-card {
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px 16px;
      margin-top: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: all 0.2s ease;
    }
    .vietlex-result-card:hover {
      border-color: #3b82f6;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    .precedence-card {
      background: #ffffff;
      border: 1px solid #fed7aa;
      border-left: 4px solid #f97316;
      border-radius: 10px;
      padding: 14px 16px;
      margin-bottom: 12px;
    }

    .quick-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .chip {
      background: var(--accent-soft);
      border: 1px solid rgba(246, 166, 35, 0.4);
      color: #b45309;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .chip:hover {
      background: var(--primary-soft);
      border-color: var(--primary);
      color: var(--primary);
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .form-group label {
      font-size: 13px;
      font-weight: 600;
      color: #334155;
    }

    textarea, select, input[type="text"] {
      width: 100%;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      color: #1e293b;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 14px;
      outline: none;
      transition: all 0.2s ease;
    }

    textarea:focus, select:focus, input[type="text"]:focus {
      border-color: var(--primary);
      background: #ffffff;
      box-shadow: 0 0 0 3px rgba(225, 38, 47, 0.15);
    }

    textarea { min-height: 100px; resize: vertical; }

    .btn-hacom {
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      color: #ffffff;
      border: none;
      padding: 12px 28px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.25s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      box-shadow: 0 4px 14px rgba(225, 38, 47, 0.3);
      align-self: flex-end;
    }

    .btn-hacom:hover {
      background: var(--primary-strong);
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(225, 38, 47, 0.4);
    }

    .result-box {
      background: #fdf2f2;
      border-left: 4px solid var(--primary);
      padding: 16px;
      border-radius: 8px;
      font-size: 14px;
      line-height: 1.7;
      color: #1e293b;
    }

    .citations-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }

    .citation-card {
      background: #ffffff;
      border: 1px solid var(--line);
      border-left: 4px solid var(--accent);
      padding: 12px 16px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .citation-title {
      font-weight: 700;
      color: var(--primary-strong);
      font-size: 13px;
    }

    .citation-art {
      font-weight: 600;
      color: var(--warning);
      font-size: 12px;
      margin-top: 2px;
    }

    .citation-file {
      font-size: 11px;
      color: var(--muted);
      margin-top: 4px;
      word-break: break-all;
    }

    .badge-alert {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-weight: 700;
      font-size: 12px;
    }
    .badge-red { background: #fee2e2; color: #991b1b; border: 1px solid #f87171; }
    .badge-yellow { background: #fef3c7; color: #92400e; border: 1px solid #fbbf24; }
    .badge-green { background: #dcfce7; color: #166534; border: 1px solid #4ade80; }

    .tab-content { display: none; flex-direction: column; gap: 20px; }
    .tab-content.active { display: flex; }

    .loader {
      display: none;
      align-items: center;
      justify-content: center;
      gap: 10px;
      padding: 20px;
      color: var(--primary);
      font-weight: 600;
    }

    .spinner {
      width: 24px;
      height: 24px;
      border: 3px solid #fecdd3;
      border-top-color: var(--primary);
      border-radius: 50%;
      animation: spin 0.8s infinite linear;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    footer {
      text-align: center;
      padding: 16px;
      color: var(--muted);
      font-size: 12px;
      border-top: 1px solid var(--line);
      background: #ffffff;
      margin-top: auto;
    }
  </style>
</head>
<body>
  <div class="app-shell">
        <!-- LEFT SIDEBAR CHUẨN HACOM -->
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark" style="background: #ffffff; padding: 4px; display: flex; align-items: center; justify-content: center; border-radius: 10px; width: 44px; height: 44px; flex-shrink: 0; box-shadow: 0 2px 6px rgba(0,0,0,0.15);">
          <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAKAAAAB6CAYAAAA4alhkAAAtIElEQVR42u29e3RdR5kn+vtV1d7noZf18Eu2E9uJHccOdMABgpNgOyQ4TkJPdzMyMIEFNEzSPOx0oIHpuff20Wlu337wSkgIa5jm0ff2XBiJYYCGENvpK5shSTdgoME2wY8EJ47ll97SOWefvau++8c+R5ZkyZbkxFbkU2vtdZblXbtqV/329/6+ImZhEwFJyM/+y73evJXpPxHgbTaSa5zIHAAeRARECDAUgSXEgpRLM1kogWgQHgEPoIaIKKVyJDuNwVODQ+Gj1971xZ+JZBSZdbNprzj7wCcEWnn6yVzVQKH4nZqqxK1BECG0Ds5JjD3Gr06WFoC85F+MxD/D8yMJrRR8X0Os5PuHgntX3fnIP842EM4+ALa1aG5ptwe3b3t0QVP1B4+fHigCMABJnvW+IjEVuuS7wHH2QkQEgPU9Y0QkDMPi6qs3PXoYyHC2gFDNJvBlMhnFLe322X/+2JVa8/2neoYsSI+kIkERwLnSJYATUAQUnLnIcS6AFJneNc7zgNFjioBuzNxiwkySNMUwCqvTvqe0+SgJ2bVr9uzbrKKA0pEx3JiNDmzf9omGuuTf9vTlI5KmTOo8QyS8Mtk78zuyBaEMA6Ako0F8BXicFqVkwY7qJwAShtBqnI0okUEnQL4oozi07ykERXvKFoauvvYPvjpQlnNf6XtmZhX/3QUHAIrYHEYu3qJh8AHHuiP89sVQjCY9TRgNGE2QEJEYHFcvMKxKMAahADCEOZKDOlmAGDV5EErMX+w11TGAS883Cjh0PETPoBOjY9hZJ4gsEFpBMYJUJ8nXLPPPgJNgMbSuOu3PGwRvBLAT7S0KaLcVAM4g5YOk2/v4Aw0i0fVBEBECBcY6RhgBjzw2gN8eC5nwOHJzwZgVwjrgr945BysXeSgUY74oKYPE9pNIffsopNYHrEwagOIRfQ++GrIwARRjRcM3xPd+msPu/QFrSkA/o4DEYAtCwf131+K2VycxmBeomFo639dkoXgLgJ2Yu3pWcK9ZA8D29i0KgE140aqkNnMKQRQjUoC0T+x9PsQLXRGaatRoFjuiWTeOQiwAPELSBpLWUwbgeEKOb4i0T6R8njUXpQBF4CcHA9x6XfJMf5LWOsLhBgBoP7VfKgCcQW1umSJYrE6mDYIgsgAMBNAaOHI6QmgBB0wIwIn+DsGw1jLxTeP1mdDqMuHjxAFaAcd7LAYKDr5hWVVnMXSg4oqOjozZuDEblURHqWjBM6BtOMNUVxJjpHMBTvTaV4oRHVoR/XmH/pzAqBIAhYwiCxFpXoqhppLYUTHDzBwExiyJkKVO5AznY8w1e4cc1CuEXigVa+P9eQdV0ntI0DoRz+h0GAUL4ztbWQHgDGmtraulREEW2liYK1s2YC0wWCgB8BViG4scMJg/a84u4WsoJwtiwXd/BYAzZc+y2awrebEabexyG/ayRU6QL8b/+UphWs4BudKchyctIlorAGoeAOyaBZqwmiXBBwCAF55+IAmy1jkZ1mZJILJAMbz0Lt+pkEABYlPQWNMiCYE0jpZ7KwC81BCMf/qRApCOgw7i8BYCsE4QWgFfYY6fYiTj82fBnNkiOqnZIf/Fwng+zKVEJOlGaoeM7Xvj2vhmsn9UYuM5xooNAlChugLAmQTA4Z1TCZJG5IyXmyg7+WV4Y18pLRpjJCyLgwKkY88jKoboGSW4a99TIoaIwVYmhE4ktgnzAj5TzfiailSgL4zkWgc5e9YCCPzZsmezA4CtALKA9pxWQpaAx5FKyrRttgSYd2BfWCJLMnkA+hemdouM88kIQEVTAeBMlJ1CTRgZxWeH2dZ0gKAIBg7BjfWwjR4kMfVoGKkq+Y+nYQQfb86lAFpVAeBM1IU9KxCOK9RPSwEhgKJDuHYOwhsbMB5DPB8ImYsm9AlPP4BTpALAmSgDRuLUGdeBlCKPz+R+XAALRm6avuQLkAOVGh/yAtgKAGegGqwcQyGsUtROZHjrlGLsU5VpKiLq0gSPazXOoCQoKFbMMDPQDBOoqAggHOm+EomjkI3ihSUhyDSvC2i+4VlTYBwYkwcqnpCZZIgWAGhIpPIKCEpxCMNyv9aEZy4gfIkjzDBTvabr1yGQKOWhcKxIIDJYYcEzMLdKFZl3QN6QdWV6IQJ4Kk4EctOlSKGAdnqahPhq6lS3BLq0P37WkQP7KgCcSfArbfCCt1TnD+3oHlCKC0oxqSxnw6USMRinZA2xAqnxkP6/n0di+3FIjTf5kHwAYojB/30V3DwfKMqUYwKrkgpjvTriBBroAiqekBmWkwSSWXdox9ZurQnGCnCJBQM1KTU9CkiAQxHU6SKkKFPPCZnGoALAaKA6OZpqC0nrBI48BQAbZkFeyOyJiG5vUaVdOqFL9ovybmoCdekSADlNU4o3zWuasYAJw/ijcaNcOqoYWmjBCQBor1DAGdTKwZmUo0pxuMhKWaBvrFFnC/TT1YCn0mca4oR1QFVCoTpJWCfliBhRSrFYtKH2eQIA9u1bXaGAM44XOzzHMRsqDphbq8/YAjHzo2DmVCmkS3nD5ex6oxUE0uXXzDkZa//ZCgAxw5KStMbBaExOSOSAeXUaCe8CNOGLqM9bC8ytU/BHaO4knWcUSLyw6IZsbraU5phFFDBmR1bpQ0P5UAjo8o5GTtBYo1CbUjM/MJUxlV7UYOKKCCPyQYxREMFBANi1K6NRMUTPpBazo+pI/845d9IzClLKTLIWqE0pzKtTiKzM7MD8UiL9kiYN584oTVJyKZL41WzxgswqAJIQyWTUwk2fHSL4jO8bkHRld5xvgKXzDCI3s2uCWQdUJxUWNxqEdtRUVTG0UIJfAABmSWmO2aWEbCi9j8JPPa3KBR6HKcjVC7wZnZxOxhWyFtZrNNWWqHXMkkVrpYbyYa7g9K8BoHUWaMCzrzzbhjWx8dnyyci6PxtWRBhnmC1fYFCbUihGMiPlwBiAwIqFBimPGChVxiLhkr7RQ/lw/+rND3aWje4VCoiZFpSwTwAgFP7rYK6Y04paBFIuzzavTuPKuRpBJDOzSoLEhYnWLPFHGc1FRHxPC4kfAQBmiQIy6wCYzWadZDJq9eYHOwXYk0p4IDFKDnz1Uh/Wzjw5kIip37xajRULDYJwFJVWYWSpwB2zSf6blYboshyoiMc874wcGLNh4PqlfuxjnWEMjKWCRNdd4aG+WiEqKSBxeV6tBnPhqSDtPwUAaGl3FQDOXAA6ALCU7w0MFS1JPQzAUHBFk8E1pQqoM4kNS4n9vmFlYhT7JcSmkp4AsvPamz89IG0tejYYoGctAMmsy2QyauVtD++PrP1ZOuXFZSvLm6yBm65NTD8w4WVSPoJQsGy+wbWLR38cQtI5oQDfnC0FiWY3BQTQWmbDgv/HN5plNqxUXH1+7fIEljTpGVOwSJWUpPWrk0j7I8UDcQlP6/6h4IVkn3kCADZszNoKAGc8G261iD0gbX2DhT5jtC4dRoTIArVpYuN1SQThpWfDJBBEwMIGjXWrEnEZOTXMll065QHkP16x5fP5jo6MIWYP+521ACQpIm165Z0Pn3Ii36xJ+wTEDlPBQLB+TRILGzSC6NJSQcW4DNvtr06ivlqN9H6IUtQDg0HgxP1XANiwC2627dXspIAAgH0CgA7qocFcMVKKCojT1kML1Fcp3PXaFIJLqIzEsh9wRZPGra9KIRfI8AE2ImJrqxOMrP3Wqk2PPCdtLZrZbAWAryRlRNpa1DVveeg3xTD6Vm1VQonEVFArYCgQbHxVEiuaDfLF4bM4LjL1I4qR4A/fkEZtmrF9cjgnhCqXDy2h/kYAts/SfZrFFBBAy2oRAUXpv8wVorBMBYE4VSPhEe+8uWpUjcuL1TTjutVrr/Jxy+okhgpnPgIRiWqrk6pYtN+4etMX9qKtRW3Z0m4rAHwFUkG0x1SwEIZ/X1eTHKaCikCuIHjNMh+3/14KA3k56/y2l7sIeXVS4V1vqh6deFQOPMgFeY/yFyIgWlYLKhTwFWqS2bdaMpmMomWmfzDo8j2t4iD92PuQKwrecXMVls2/eKyYisgFDu+8pQpXztNxLWgOI9DWVSdVGNlPL930yHNA26w7pPqyAmA2m3Wta9Zw5Z0Pn4oi94mqlK9G1qu0Dkj5xH1vqYGnMTYG72U5A6Q/57DxuhTecn1yFOUVEZdKeaa3L3cwUeP9jUhGAVvcbN6fWQ9AAOCWLVbaWvTKOx7+as9AYUddddK4kaw4EKxaZPC+W2teVh9x2eNx7WIP77u1Og44GMF9laIjCefcvVes+3we7fs5m9xuly0AY6tMrJDAmQ/kg7An4WlKiRVrBQzkBevXJLBsvkEhfHniBYnY43HX2hRqU0Q4wgbpnNj62pQZygefWbH5i7s6OjKGs1TxuCwByGyskKy443Mv5Irhf0wmPKVAN5I6RRYvu02wFOEcF03lcA1rW1udMD39+X9d4Tf+ubS16A0bsvZy2JfLhwIC4JZ2Kx0Zc+0dX/wffQOFT9fXpYwIwrE1Zi7mUfUi4hKeUUEYdRUjvoMbsxFaVstsZ72XJQABABuytqMjY1be8fAnenrzP6ivTXrOSTQptEwXZZiwoI1orURrSD5ffPu1mx/6XRxulXWXy3aYyw1/JESk1WYyUHn/1Ds4FPyoribxmv6BIJqo+jyLbupAVATC0oHAHDf+TxRpq9O+6e7Nf2DVnY/+s3RkDONzgC+bdvlRwFKwQmsrcN3GRwcLIe8qBNGh6irfyFhKyNhlEi1Nx0CKZHJCoiY4EMLNT0BqvbOOdijlqdi62qTp7c//+ao7H/nK5Qi+yxaAZS9JW1uLXr35wc6+XLCpGNkjVWNBqAjmLAp3zsfgAyvigzvyduLKpyquhs7eEOHaORj4i2tLxzSMTDCKwVdfmzQ9/flPrbzjkb+5XMGHmZ2ifXGatLVobmm3v35s61V1KbPD9/Ty/sEgUiPZsYsLVZrf9KPq0edgDg5CakwMuDKLVYzBCSD/h83IvXNxiX3L8GcuIkJFN6c6qfv6C3951aYvZDo6MmbjZQq+CgDHgvB/fnBJbV3iB+mk96regSAk4WFktdS0BvMWqf/+IpKPHQcDB6nSYChAwSJaUY3ce69AuLYeHIxGnSviRJxWZHXa50Au/MTVtz/06RL4LHB5aLwVAE4ChHvb3t9Q01TdXl2VvLW7NxcB0CxXPXdxtUtJG5hnBpD69jF4e3rgGnwU7lyA4C3zICkdg28Em3YiNukbTYUolwv/4zWbH/n65U75KgAc1yySUWTWdXRkzFLX+6XqdOID/YMBnHPD2XWQEktOa4CEeXYIrt6Dm5sAh6LYwqyGzzMSiNjamoQphq6zUAjvWXHHwx2Xs8xXAeB5WiaTUa2tWSEhh3du+5Dv6c9qrZJDQ8UIpGb51OtSDJUkNRgJELpRVE9ELElVX5vkYK7YMZgrvm/N3Y8eqVC+CgAnd0ple4vilnZ78Icffm0y6X0plfJf3z8YwFoXASOAKKNXUkQcAKmpSugwtGFo5a+W3/bgpwC4MpuvrHDFDHNeYzW3tNuOjoxZsfmLP3/sQO7moaHgPxut+ubUpoxWpIhEAlihOIE4iEROxKWTnqqrTuqgaHcN5e1Ny297MCsiIpmMqoCvQgGnLRcCwG+//8HlqXTy407kXdVVfnUUOYSRg1KE7ylEkSCM7M+tc59Z9uaHvgEAFZZbAeBLsk4ibYrcYgHgd9s/skz53r93Ihudk2UEBrXiL6j4nb/vqH08m826+LDpDC8nv26lXQQFRdpa9JiAAo5n0qmsVqW9rEDs6MiYOGQ+Pn6koyNjSsCrcJVKq4gxlVZplVZplVZplVZplVZplVZplVZplVZplVZplVZplVZplQaApZSaSVvzWwFkMbpWcQZQrVMbVyYqth3PJ0NgP4GTo+a1C8AGzDur3y6c5Iaz/gZswAYHZGUyhb3L4+7CLjX+syY3LjBP4rOLzz9uPGaLGu89Mc6Yu0r3jT9muxDj15AWtOixY4zXdgHYiN1RnEbVMrz+5fcf/b7zBGh35Xcc+y4j1+xc/TCzjkp7eZz4ghYtE3xkAvDlHHe8v2cA9XKMKQDbLvC5MkXXYry2Ux+z3IenF67bWqP0lgGxDucJUPWoEDrXG7rBdyw88ashADi8fG1dXT7xTY+qOjx/EXfbSKO7JPpK07Gnvi5o0cToIM0OrDc3LJZrRewKcVwcwc1VZK2DVAFMUGAEos+8CB2JkECBQA4ifQrqNBVfVHCHjqVqnll56PHgfBN7fvGNqQbrXSt0V0fkIifSBEgtBGmQvgg8QtQZBzCtlMYVSE4Je0mcUqKO+iIHE8d//Mx4FKlUk0gAoH/h+iYgvFYUl4njQkdpgKBGgBQpvhMYlgAhgICwFBRJFCBqEEQPxZ0w4BEt7kD6+NNHygDPAk6QUUTWnW6+6Y/raNb0udBh+BCI0YwwpciCsycaO5/6u+4Fb7zS0FwPyCqhWxyB9RDxSUYUdivK77SoX4uLflFz4umTANDX/OZGxcKrrGANhEsdpMlB0gSoyAKAHgU8r8Bf9kv+6UWde3IZQBmCq3yam9MA9DnALwB8Et2QfKLoDefMJvPwANxWTW1CqHN+PhEEUAZ0UYnLxOS6xMKlu3ndAwnae0OHldVKU2sC0KMi3wWAjYPt4lPEyeGvZuTYFoIhIRbmBg/3LbzpH2vrm/8v7G8PS/eJAGwF2Lq6xfT2df4fxuFdVsnSNE08IkeXjnYA3Ihxz8Tkjx43gmDIORc13/LMaXH/tanzyQdLaUouU/rtXnjTFT751452k4ZuTFBB6dFrjdJ7ljM7JxpToBGKoADmhppv+emgRH89v/Pp7TEb3V/Ojnq3Md6GOsq4eywAFIg8nTu98KZNinydR9T41CD0qK+ovNZFERSpe04vvGl7PJ1gA8D5aSpodXa2Akf0q2fVc6ebb/o/m449+VVDMF+UyObE2uHdngCDHkhS+hy1nBHmlFDQNyDRnAhyvgOwoqTQiDAYSYqJdnv/wpv+U4P2/3rQhbAQ9LlognxZ6mpqhhAYEP0ugkCicc6hJkCtyKtqdSLT3fvi4kbgAzGLardAi8qi3W7tOfZgo0l8sN8VEYpIn4Ru5KN4ZoNMihq2NG6fi1y5vuDZEf3UQlndqP3Pn25eV8tjT/2lYL0Bdts/mX97lWNue5XyVvW6IooQVxA7skx0uSIIEkoZAw6DcMBF0QTnbSsFpj2l1teKWX9ywY0bePxfdu9dvc/HflgQvaErRv3xmuqJzqpTpGkwiVshDpE49LhIALHE2R+HAMqDqq/T5h0sES8LgRMZ7ocR1H5kvxT1sjnKfOXUgnVFJRBFUJcqmkx4ofQr47yAlPriHP1HjlEG6R4MEmh3bbGM9v68i2wgLoq/GGqCpnwB1BrUBhgaEPuRSOT2HOx7FHDKg9Iy5v64P1AUsb02sCJ89/F5b5i/Be02Zk3ttufK9XNI3NNvizYUZ1kCz8jnCKj9mFMcyzt7T0Hk9pzYj2igoM+886hxASAQFw250FJ434Gr70i0YrcjIL4q3DxHmVVdLijaWBlTGN3fCKCqlDZW5EcFcb+fd3ZT3rmvpaiNgGrMeIagEkD6XRQkqGCUuhcA/OIVZVKk4zWEGaevIWgUqTUQddvCV7pd+PE+F31GAwMGykj8nmbkPBWoIoj0uzAadFHQbcOv9bjwE/1xv34DZWJ2f3a/gtioKM6R+PglrY61di3APRBZ+GyiG4mqCKJjxXz8bzRJo4bEHph77Mkvlv/a1XzTPdVUb+mTyKK0+WPIoBKAIJRRaABwYhd2KQBOilGtQBKOONe4Lq207nXhT5s6n/5/S398oqt53YdS1Ktz4tz4VJ86ElAg6XSuqzoLdMXSlp0rUCXgTcgtXIpKDbnov83tfPqfAKBn/usPhvTex4nldAIwUZyW1wgARf95maTi4ZJUKhB3tPHYUx8YXtuF61bVanN3SXYcj3JKgtoUxB1t6nzyj0f0W16nzR/1udDGADx7bQIRElhySQE4ZhEiQKJy/Z7xNiWm1rAdWG82YJ7ahZOOEirhZG0/Ss76t9jJzA0Qmg6sN3MxT60BbDde5GQjVavVGZEFhHASmqbEV6qsLfZIZ41MwnLBM1LD1KNqBdEB3JFYgecFmOu6EbnJ9hO0+MA+TKYfzwgr0zsZIxcpI1hvBOtNEKkLB7ELSWBujfJMvTJeg/LM2GuOMn5K+QZAU2xfGuAGzJOLaEySjdgd7QdsSXMXAVxJ0z3rGvF3mX7OLB3Rbol2K7QXI7mJLyJvgf0RsTuaIn6n0286BSopV/T/S3f5X20ncfrWheumt8h7quN+J7yiLJRPDrioOnIiDhLbCqjoIKpkt3ZpiqXgSAkAFgC6edOlyjrzE1QqwvhHiwgAD0QEl6j4O14CABKgFQFEarsWrvu6kMXSUichqHIQcJr5EcSeEJ34wmTu7V18Y0PfolvuorjXOPC1AnnDkDgZ3771srajRedSoTg3gVwmLq463S86UUnNfCkooIvtbslq6vdwxJc+CHvB54juXb3aX7O/JSLiPFrBWq9vSeIKY9W1EfBaQF4rwHXWYWk1qY0yiESQE4sS+C9Kayn99nve5gYb8PQ57l0CADohOLI76MB6s3GK7KkCwAla+BK78QQg9+8vPrV4e2pIbrnTOrmzj3i9RHKVUSqVJmEBFMUhEIcBZ0MhTIqKBCEXEYDltvTI7mAYZOfnHtJRwdqFA5AxFQzzYn9CMColZnsgXq9i+9U0wBe7i7qa170xKfrrPrmSWiEQhyIEgxI5xEdrUQAaKFWrlDcoNheIfUaAJR7U3BAivIgpkryMi0peEgAKIB7JokhP47FgI7EnBIAXF65NJyRxVJP1UwXBHgxyLbIiyKguPPHlNPXK0y4MS5YKVfIqKMS2PDGxGb9/SNyfJmh2Vr24++jp5nU/TFPd0SfRRLaql7S1n7E/fi5JtSjvnGB8sxE8KESQXBSZrfNO7R6qwO0lYcHC3rqoSvrQDwCdYqvA6VGeM4bo76coibn9EjrG1npObIh2B5uO/fhrI+LJPOElqVq0Ja3NIo8OE2nBBkSXK0rSy/0ZgcEK3F4iGdDqRNnOhaPKcy8NM6JVoIrNa+difUJBi96DZ9UNMRW+JKxQiJ68C+fnRRxGRMmMNFcZgBD0idYVdo0ZXx9w8nSMaLdrsfySmjYIaMRyryn7O0deZ/4OfTHWpALAi7f1Lg41GjCCFo2Ld6aaCFr09Rgwgoy6GJRXUdmyx4kilAoLfplaM0J0MohjBiYO6YrNLZKO2X8cZNol6/wLoRM8H88vIY1k4owH5vFJjSvlH3WWgcBNUvFLlV1bfebmoGQCO6eiJ68w7fzSAnBPtQgyinuy4enmdUcS4JUBJALojV1kgiovTjSwqqv5pu8I5BcUziPw+pzYKXlCSj5kvqDC01VO9SSoFuTFhTHbBEePTTXorCjBm7qa1/09hEcFcq0ilxfEyVgvSAkAAiBKkL4Vdv3ieT1QNjc5pQ45ESWAi2PmSl7H0WPqAWdByCdONd90hRL0RHBv8qlBOesDLX1AIhCEnlZJFfF3ALCmeAWB/TMbgAK6UkCnPRcxIFiOUhkvfMSWniHnklsIRKUY3xEUII7aFZEHleL6Gho/5ywiQAhxZQpVCvFgBLJO6X9nqP8doDDgAgTibKw5nx0gyjIBG/Vy7QK0qCuOtue7Ft7c6iv1XxJUfkEcQhHYGEPDgQQuDof3a2jer1R89NuQRJajjiIkGcd705BMUvkCARU+tRG7ow4gJoMv/vinp5vXfaNJJ95ZFItAHCKReIx4ilKmdAqcW0e9lQoIRFAQG5Ud//F6UBGgB8KjYkrp5KCLTlu4hwQg6k650tScxIGldjwCSdDFY49ZP2Ja/UqYsoxxwYn2RCDOKEiVr3xTLTTnC8k3JLps2KBGBMlSHEE21ikP0Xk8EhHEKOWBrpAeqVAIQHY+/Z3O5je+tRbmYwRuSFNV+6QeGeTvAISxJyTQcC8UxT1FYGOT9pcUxE5oDWKp75ArqJHjZgDV2PnjL5+af9OBlFbvj+heL8BiD0z7VEqD4IgweCcSn1UDoF55WkpigZM4BSAQgYMMRoKjgdifDLnoq/OO/8vuOA9kd1QGa9Oxp+7pbV63w0BtcZBXCTA/QeV5YGz0LI1ZTj8QAXwQKeUZiT9W2FL4fyBOLKSHgmdzLurocsUvLT3xk+cEIPYsd8AeEJL2aHSSosfbYwfoFBUCFKvHrNuk+hXO6idpQ6MTE/QrRfpgQKIanlrwxtfVa+/afoTnPArSAUgCyIkEc48F3y4bog9cfXViztDcP0oo5YXn0WosnDTBYw/cLxte/PGvRibolBNpAGBo8Y2LaM3SQGS+KNRQYECxpBrSkFOG5mgymXqBhx4Puhfd9Hv19BZ02aLwPFpj0VX/eOGJnUMyOlRclU1KgvUmtziYX3ScZ8g54XCCkPIpME6cLn3hAopVgtApFRAu5zkMRNr0+kpOVz2/4GQ52Wrk88f9sBfene7zehfAsQnW1QlY5YCUUHwAmhKbeIR0ACyFRQUpOKicoe2nSI8wOlV37KddYxOfyr8nF9742nqdnNt3jjVKaIOitbn6zqd+XKZSPc1vfE21Ssybar8Tzeuub1D+/HP10zAQSjTj0jKnkhb4UqU2Tje18HzPPFeKZDxmRr20Y6438gqzbDCe8PpJT3oX4uRljEml3DClYXe7c1GFOEuuhWMTv3cNJzu3Szm5Pd7E/Zyk/fCcAaLDmXLIDMum4yefT5S0HiekT8VXXC4M0I4Wtpwz4X2ipPUza3Euf/sU1she1H4yRmzjBHa1kfdxdNZdpVVapVXaK7Px+ccfaDjafzS/ePFiSHcheeXdX+oZe9Petha/efny1BO7ny22rF/NZ3s6vatu/3LfBZ/HxkpYE2ZceZTYtzQRJ3yp91uF2n2muWnRQROpg4Hx7isfT1XulMlkVE26qaqnJ9+2bu3iAy8M9P8GNnkLALRN8UCWtrYWLdKmh89jA0SkdObGNGP5ROLDY+QlikkVyai2thY99pK2Fi0jzgbBNA+5yWSm3r88J5mgrwgo5/j/yYCjfO4JASmDT9padEdHxkz/uRk14X6XD/g5tP3+baee/ricfOrjcvjxD98+9qSfjo6MAYADP9z6D4M//3M5uH1r0Pnkx+aVF3Uqkxn17wNbE5M5dei8X9VLeGbHZD+CqYJw7DpNad3GzKm8H5Mda6pzE8koObD1ghOpxoJW9mb88dbNOIguhpETASKhLyLErlaWwbBnz5cpmYw6xG4pFCMHIIiKRX9qQBGSdM/ueGC99uTdzuF1zx5xc1nfnHv+/3tgvwO++7XdP/8HkpEIeD7yXz5A8NAT99/4wi71nxWVyRWKv7x6UUMGa1pDcmp++/LzDvzwI29+Me1/NBdEiO1vLDnj4LRWPYrqmaBQ+DaZ3TfyEMNzfSAk5L0bTs374zf96aeNpxqLoe3OF/s+ngU6z/Wu5ecf3rHt1qMJ87EocnDODUnU+QGRzEBrK9Da2ip79txn6k4n/qKmOvG6Yhj1Rm7wk1ngSGnNZTL70vG19ySXL218H8Td/dwTvdcIWPXsE/d3aeKXhUh2+uRP/EL+yKLf/3JuKvu9/7GtN1al9b1iceNzx3sacRy5I/98/z6l1HeP9RS//fo/fKRblf2dAJWhFEkKN2YjkkJSbrjhvpDZrAPh4uhkUuzko+/jhaQc2rH1c8mk2jWvoer9vqdf7azUCnBVY336rXXV/t+/95brdx1+Ytv8yX3FsalDQrcvKEbrF86rvgPEIK/LFrGrdRr2vFYBgETa7AtCu3lOTWJzVTqxqSrtb6pK+5uq04nNc+ur/kN9XfIvU+nkngOPb/0gmXXno4QkRNpa9LKNjx4vWregeeGczdZK8+rND3a2tbXoc39o8Zy05+8LitHmqrS/OZX0/r21ydvIrHtrc6fGrlZ9ww1fDqGkd/6C2k2Fol2x/M2fPZLJxGt+PgpFUn63/SPLll9Z/1Rdtf9oU336TgGucg7VBNbMbay+Z8n8mq9buO3FmpQ/ntVkPDGLpBzavu0ddVXeU/Prq98XRnaVtXDOoaEqnbhrXlP1l5sb/WcO7bi/VY30aDuw4ZnvfbTp8He3zX+m46NNz3R8tGnv9z+04JnvfbQJglTsB58CZWlr0WTWHdq+7RNN9VUPOCfoPDn4j4XB8PcSMFcUIyw70TX0yZ7+Qr6hLnWTtfLN9vaWSRe7rEtZJ4Ke/qGCFTJ3oWwjYbR1VroA2KGg+MmBgeDq/GC4KjdUXN15qu9tJ7sG/00rJpIJ8+ihHR++gcy6ycrBBPtyg4ElMCXlLaE966zrHRgKbKEY2VRKf/PA49vedsN9Xw6fPtXvlbwkudxAwZLsnazo0grgxe/dmw7B79bVJF/T3ZfvOd41uLUYYVmo7FJau7zz1MA9A0PBs+LwD8s2PtTb0ZE550cjAFta2t3etowPyF8lfMNjJwc+kVJubtDXeaWLZEnPUHHtiycGPucs6pTC901cWkkhXyhaKvUPOhFZR0AXY1uz9g0gEQh6A0NFkKIn+5Jkuz288946cfgz65wNgnD7VZsefveI27oB/N3Bx7fmB3LFh6rT/obrZeGtzGZ3TvZ0cZaLKsmFewBy+ZAC0UYpLU46V9758OER//2bA49t/Ume0S/n1CQbT/fa+wD8bO7c1ZMtDKJJjFvc6dxzKpJURkRorUSe0X4yqb95YPvWd67c9PlviWTUoR3diqSGTO7Zu3ZldDabjd69/f53N9QlX9U3UCiGTt51zVu+8NiI27oAPPfzx7burE+pEADOe+5xvOmy/9unawDdlAtCS+KgpyVYM3e148ZsP4CfA/j5gce2fmXlnQ/vf9nCsdrbWxTQbp1NrPE8NTcoWkTkF0WE+9pbvTUt2RDtLQoA9vXbr4H43+Y2VM3L54u3ANiJSW/sy2KKgFL0JZNR+9bArNmHaF8LzMrrskcPbt+62/P0HwGyBgA2bMi+zKegDwHwoRRFxL23EESfqqlKXAUn3/jt9m2GzH7z0I5tU9rHDaf2SylIZpPvKxf02l9cc8fDj/3sZ/d6a9cutAd3dt/ieYnfJnRgk0G6eLxn0Bx8/KNLjiZqOs8FQpIimYzCH6Ln0I7u39akE6/rHSj8z4Gi6Rpgz+lnd27ro+Ipz+i9ff3RV4Yjop1zSPhGi3PvsYG5UuWx3PrmSuubK4NidJUNzJUi8j9qqnyI0E4lgVsT1cYoKRYtjHOn0drK/dhvSQi2tDtuaXdrcCpPoFsrwoF1M+SodGE2607NhWM2606dgpO2Fk2wu1Q+Lnkuz9FLHP/vfM9oS/OvRtzt+SA85nnGpBP6vx1+YtvtFu6knkqZn32ry2FmdSQVyRdFMqr2ZEKRWUfBxxtqTGchUCe7JN81Z27yd2T06UX5bn1eC0ArQGYd6T40kAsOeEahYU6qcX5j1TXzm2peP6+h+q6aKv+TNVVq/8Gd97/djHSvKUj3it//3LjJ/ge3b82TUyBKLfFLinKdQTGSmnQCvaG9jtnsT57reE9S2lqwD6s1tmSLz8yZN98nFxcjRwAnprVHpJKOjPkdYKQjU/LRAtgVA2iqz3MiWjoyZlfpeXsOdJL3tUcHtm+92jkRAr0jtdWXG4POOcBGTUvveOQnv/7+B29DCturUt6SQhB+S1E9OTAUAJiceLRrAxSycBAcd06cQK4hs046MlY6MuZQsfvXhSA64JzLC/jahtrUHfkg/NXKTQ8HEpuB3MT7EJ8WT37xZwCueaHjYxv6BgpLRTBXIPMILHUit6SS3nyE4UNmZLjMCDOMxoZWWzLDmLVr740O79imR1S+O39pMmadiHDXrtbfLC5271OarzJG/affPvHA9mUbP/8iyhFaABI0f5tMmuqBwQDOuR+UvO3n3dTuvgK9VBVIwgGDjNnDWSyioyNjziu/AFCFiM7TcWgp0T/2ec/uuP/3leYbI+tIJT8qRQeoyYTYu5L2OFVbJwshJeWXsmEYZjIZ9aq7s7/Z/4MP3wZiZ01V8op8IdxcLFpw3Oy8cVjwhjWlgAl+qxBE/yGZMNc+u/P+j3Nj9tOlW/68fO+Bx//0noSvbnNWCpN1NsSy/7ablePgko2f3TX2nsM7t37Q9/TDuXzYaAQsxBHNgBZXICnS1iJlNb6jIyMk5dAPtwblyOeg6BcnJwduUVu2tEeHdmx7IJcPn6irSa7o7S88eWj7tkeFfEYgjZp4Vzrl3ZpKehjMDX3mmjse+bf4Jc4vWyXrbBgW4QpBaOncmw9s30aKaKVp4YTKM+Iie43Nd38awNHz2cbyCYaegysUQ0un7jq8fVujE9GK8IR4DYi319Ukve6+3HGQX4pNEq0WyE6GQhdBWIDFqQAwn0CYgEQC2MgyzGazbu/ejL/6uuyBff90321EegfJRQJRbpLPJrfYmJW2fufAjm3fb55bc3dvf/7vDu/ctg6QfwLkBMA5AK8H3NuDojMgN8nezCPYv99ORgE9tFM+k0p7rzm88/6vUtxT1roX4CkqYDWEH076RpN8yhBYkU75WpE4GYTLzhZY18jethYfisuSCaOTvpkTFOxiACdbce6l37Kl3ZZY1D8/84OP3Anic7XViVVVKe9vI+uglYK1Dn0DhZ5cvvj5lZu+8KnJsLTW1jhg2EV18zSxEELdVJ9+WzJh3laOwnQO8DyNk12DGCzgU+eWW1oJQAzV/IRvGgiiqSH97oSv3y0lV0TkBKd7cjI4FPwvcfjQ1Zu+cEIyGcUs3flEkQOPbU0oYklp0ZcceGxrYsXmhvDcU4rn5Cl/vqd1Q21VAkFhaDGAvWvWIOroyJg1G7MH9333Q3dX1fj/VlOV0EEhav7Z9+5Nr31raz6bPd9HkRWgFXn47+jqHnpYad4zv7H6D0j+gXMOSsXR4CdOD7rO0wNPUPA1FDoFLe3uPAZoe3TnhxtFeKQQRCvmN1b9Cck/KYYxI0n4BvlChJPdQz+KxL3XKCUHuntzH00lDGHjagfYEg8S8/It9vnHH6hznvunzlNDP6hOe6oQBjXlQ2smw4rb2lr0qrse+eHetg/9Lz2Xbx3KhW9wIvO0wqBS3FsIgsdW3PHoobIF/fyH5WSQRRYK0phKJz7ZP1R08eufyU2gUzSGEkZ2tfa91PkO3wEAz6HWT+qPDeYCN5grDj/Po3Yg+o2nDyx502f/tWwsP59sGa9f1h1+Ytsc36hvHHmx978nDCXybD2ZPT4Zrw9h6nxPfSyXL4Iss+9W2bCRVjIZ9Wy6cBQuuL+nJ+d5CY16JptIPn8+ak/GeLl+E4YA/PGRjj99tKsvf7u1bgUgSYKntda/IsxTS9/82f2TlMMFABbd9sVuEm/f+/0PLejtL9wSWnuDCBYDgNZ8AcSTy2/7wvdJyP8PHthrKSnJ9hgAAAAASUVORK5CYII=" alt="HACOM Holdings Logo" style="width: 100%; height: 100%; object-fit: contain;">
        </div>
        <div>
          <strong>Hệ thống tra cứu pháp lý</strong>
          <span>HACOM Holdings AI Copilot</span>
        </div>
      </div>

      <nav class="main-nav">
        <button class="nav-item active" onclick="switchTab('queryTab', this)">
          <div class="nav-icon"><i class="fa-solid fa-magnifying-glass"></i></div>
          <div>
            <b>Tra cứu pháp lý RAG</b>
            <small>Hỏi đáp văn bản luật có kiểm chứng</small>
          </div>
        </button>
        <button class="nav-item" onclick="switchTab('alertTab', this)">
          <div class="nav-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
          <div>
            <b>Cảnh báo tác động</b>
            <small>Đánh giá tác động văn bản luật mới</small>
          </div>
        </button>
        <button class="nav-item" onclick="switchTab('graphTab', this)">
          <div class="nav-icon"><i class="fa-solid fa-diagram-project"></i></div>
          <div>
            <b>Đồ thị tri thức</b>
            <small>Liên kết mối quan hệ giữa các luật</small>
          </div>
        </button>
        <button class="nav-item" onclick="switchTab('uploadTab', this)">
          <div class="nav-icon"><i class="fa-solid fa-cloud-arrow-up"></i></div>
          <div>
            <b>Quản lý kho luật</b>
            <small>Tải lên & nạp văn bản mới</small>
          </div>
        </button>
      </nav>

      <div class="sidebar-note">
        <div class="status-dot"></div>
        <div>
          <b style="font-size: 12px;">Hệ thống: Đang hoạt động</b>
          <small id="sidebarHealthText">1,145 Chunks / 16 Nodes</small>
        </div>
      </div>
    </aside>

    <!-- WORKSPACE CHÍNH -->
    <main class="workspace">
            <div class="repo-banner">
        <div>
          <h2><i class="fa-solid fa-scale-balanced" style="color: #fde047;"></i> Kho Tri thức & Dữ liệu Pháp luật Tập đoàn HACOM Holdings</h2>
          <p>Hệ thống RAG & Knowledge Graph phục vụ 7 nhóm dự án cốt lõi (Đất đai - GPMB, NOXH, Năng lượng tái tạo, BĐS nghỉ dưỡng, CCN, Đấu thầu, Định giá đất)</p>
        </div>
        <div class="repo-badge">
          <i class="fa-solid fa-clock-rotate-left"></i> Cập nhật đến Tháng 08/2026
        </div>
      </div>
      <header class="topbar">
        <div>
          <p class="eyebrow">TẬP ĐOÀN HACOM HOLDINGS • LEGAL COPILOT ENGINE</p>
          <h1 id="pageTitle">Trung tâm tra cứu & cảnh báo pháp lý dự án</h1>
        </div>

      </header>

      <!-- TAB 1: RAG TRA CỨU PHÁP LÝ -->
      <div id="queryTab" class="tab-content active">
        <div class="surface">
          <div class="surface-title">
            <i class="fa-solid fa-comments" style="color: var(--primary);"></i>
            <span>Đặt câu hỏi tra cứu pháp lý & quy chuẩn kỹ thuật</span>
          </div>

          <!-- BỘ SƯU TẬP CÂU HỎI MẪU NGHIỆP VỤ & TEST CỘNG SINH -->
          <div class="prompt-gallery-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
              <div style="font-size: 13px; font-weight: 700; color: var(--primary-strong); display: flex; align-items: center; gap: 6px;">
                <i class="fa-solid fa-wand-magic-sparkles" style="color: var(--accent);"></i>
                <span>Gợi ý câu hỏi mẫu theo nhóm pháp luật (Bấm để tra cứu ngay):</span>
              </div>
            </div>

            <!-- FILTER TABS -->
            <div class="prompt-filter-bar" id="promptFilterBar">
              <button class="prompt-filter-btn active" onclick="filterPrompts('all', this)">🌟 Tất cả gợi ý (14)</button>
              <button class="prompt-filter-btn" onclick="filterPrompts('KĐT', this)">🏘️ Đất đai & GPMB</button>
              <button class="prompt-filter-btn" onclick="filterPrompts('NOXH', this)">🏢 Nhà ở xã hội</button>
              <button class="prompt-filter-btn" onclick="filterPrompts('NLTT', this)">⚡ Điện gió & DPPA</button>
              <button class="prompt-filter-btn" onclick="filterPrompts('ND', this)">🏖️ BĐS Nghỉ dưỡng & Condotel</button>
              <button class="prompt-filter-btn" onclick="filterPrompts('CCN', this)">🏭 Cụm công nghiệp</button>
              <button class="prompt-filter-btn" onclick="filterPrompts('DTT', this)">📑 Đấu thầu dự án</button>
              <button class="prompt-filter-btn" onclick="filterPrompts('TC', this)">💰 Định giá đất & Tài chính</button>
            </div>

            <!-- CARDS GRID -->
            <div class="prompt-cards-grid" id="promptCardsGrid">
              <!-- NHÓM 1: ĐẤT ĐAI & GPMB -->
              <div class="prompt-card-item" data-category="KĐT" onclick="setQuery('Thủ tục bồi thường GPMB khi thu hồi đất quy định như thế nào?', 'KĐT')">
                <div class="prompt-card-title">💡 Quy trình bồi thường, hỗ trợ tái định cư GPMB khi Nhà nước thu hồi đất</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Đất đai & GPMB</span>
                  <span style="color: var(--muted);">Luật Đất đai & NĐ 102/2024</span>
                </div>
              </div>

              <div class="prompt-card-item" data-category="KĐT" onclick="setQuery('Bảng giá đất mới theo Luật Đất đai 2024 được áp dụng từ thời điểm nào và nguyên tắc định giá đất?', 'KĐT')">
                <div class="prompt-card-title">💡 Thời điểm áp dụng Bảng giá đất mới và nguyên tắc bỏ khung giá đất</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Đất đai & GPMB</span>
                  <span style="color: var(--muted);">Luật Đất đai 2024</span>
                </div>
              </div>

              <div class="prompt-card-item" data-category="KĐT" onclick="setQuery('Điều kiện để doanh nghiệp được giao đất, cho thuê đất thực hiện dự án không qua đấu giá, đấu thầu?', 'KĐT')">
                <div class="prompt-card-title">💡 Các trường hợp giao đất, cho thuê đất không qua đấu giá quyền sử dụng đất</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Đất đai & GPMB</span>
                  <span style="color: var(--muted);">Điều 124 Luật Đất đai 2024</span>
                </div>
              </div>

              <!-- NHÓM 2: NHÀ Ở XÃ HỘI -->
              <div class="prompt-card-item" data-category="NOXH" onclick="setQuery('Định mức lợi nhuận dự án Nhà ở xã hội là bao nhiêu % và được hạch toán thế nào đối với 20% thương mại?', 'NOXH')">
                <div class="prompt-card-title">💡 Định mức lợi nhuận tối đa 10% và cơ chế ưu đãi 20% đất thương mại NOXH</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Nhà ở xã hội</span>
                  <span style="color: var(--muted);">Điều 85 Luật Nhà ở 2023</span>
                </div>
              </div>

              <div class="prompt-card-item" data-category="NOXH" onclick="setQuery('Điều kiện và thủ tục phê duyệt giá bán, giá thuê mua nhà ở xã hội do chủ đầu tư tự xây dựng?', 'NOXH')">
                <div class="prompt-card-title">💡 Phương pháp xác định giá bán, giá thuê mua NOXH và cơ quan thẩm định</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Nhà ở xã hội</span>
                  <span style="color: var(--muted);">Điều 87 Luật Nhà ở 2023</span>
                </div>
              </div>

              <!-- NHÓM 3: NĂNG LƯỢNG TÁI TẠO & DPPA -->
              <div class="prompt-card-item" data-category="NLTT" onclick="setQuery('Cơ chế mua bán điện trực tiếp DPPA theo Nghị định 80/2024 cho dự án điện gió và điện mặt trời?', 'NLTT')">
                <div class="prompt-card-title">💡 Điều kiện tham gia cơ chế mua bán điện trực tiếp DPPA qua lưới điện quốc gia</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Điện gió & DPPA</span>
                  <span style="color: var(--muted);">Nghị định 80/2024/NĐ-CP</span>
                </div>
              </div>

              <div class="prompt-card-item" data-category="NLTT" onclick="setQuery('Quy định về giá phát điện chuyển tiếp và thủ tục đàm phán hợp đồng mua bán điện PPA với EVN?', 'NLTT')">
                <div class="prompt-card-title">💡 Khung giá phát điện chuyển tiếp các dự án năng lượng tái tạo và hợp đồng PPA</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Điện gió & DPPA</span>
                  <span style="color: var(--muted);">Luật Điện lực & Thông tư BCT</span>
                </div>
              </div>

              <!-- NHÓM 4: BĐS NGHỈ DƯỠNG & CONDOTEL -->
              <div class="prompt-card-item" data-category="ND" onclick="setQuery('Quy định cấp Giấy chứng nhận quyền sở hữu (Sổ hồng) cho công trình Condotel, Villas nghỉ dưỡng theo Nghị định 10/2023 và Luật Đất đai 2024?', 'ND')">
                <div class="prompt-card-title">💡 Cơ sở pháp lý cấp Sổ hồng cho căn hộ Condotel & Biệt thự du lịch nghỉ dưỡng</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Nghỉ dưỡng & Condotel</span>
                  <span style="color: var(--muted);">NĐ 10/2023 & Luật Đất đai</span>
                </div>
              </div>

              <div class="prompt-card-item" data-category="ND" onclick="setQuery('Điều kiện chuyển nhượng toàn bộ hoặc một phần dự án bất động sản theo Luật Kinh doanh Bất động sản 2023?', 'ND')">
                <div class="prompt-card-title">💡 Điều kiện và thủ tục chuyển nhượng dự án BĐS thương mại & nghỉ dưỡng</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Nghỉ dưỡng & Condotel</span>
                  <span style="color: var(--muted);">Luật Kinh doanh BĐS 2023</span>
                </div>
              </div>

              <!-- NHÓM 5: CỤM CÔNG NGHIỆP & MÔI TRƯỜNG -->
              <div class="prompt-card-item" data-category="CCN" onclick="setQuery('Trình tự, thủ tục thành lập Cụm công nghiệp và điều kiện làm chủ đầu tư hạ tầng kỹ thuật theo Nghị định 32/2024?', 'CCN')">
                <div class="prompt-card-title">💡 Quy trình thành lập Cụm công nghiệp và lựa chọn chủ đầu tư hạ tầng kỹ thuật</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Cụm công nghiệp</span>
                  <span style="color: var(--muted);">Nghị định 32/2024/NĐ-CP</span>
                </div>
              </div>

              <div class="prompt-card-item" data-category="CCN" onclick="setQuery('Quy định bắt buộc về hệ thống xử lý nước thải tập trung và Báo cáo đánh giá tác động môi trường (ĐTM) cụm công nghiệp?', 'CCN')">
                <div class="prompt-card-title">💡 Yêu cầu về ĐTM và trạm xử lý nước thải tập trung đạt chuẩn xả thải cụm công nghiệp</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Cụm công nghiệp</span>
                  <span style="color: var(--muted);">Luật BV Môi trường & NĐ 08</span>
                </div>
              </div>

              <!-- NHÓM 6: ĐẤU THẦU LỰA CHỌN NHÀ ĐẦU TƯ -->
              <div class="prompt-card-item" data-category="DTT" onclick="setQuery('Quy trình đấu thầu lựa chọn nhà đầu tư dự án đầu tư có sử dụng đất theo Nghị định 115/2024/NĐ-CP?', 'DTT')">
                <div class="prompt-card-title">💡 Các bước đấu thầu lựa chọn nhà đầu tư dự án khu đô thị có sử dụng đất</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Đấu thầu dự án</span>
                  <span style="color: var(--muted);">Nghị định 115/2024/NĐ-CP</span>
                </div>
              </div>

              <div class="prompt-card-item" data-category="DTT" onclick="setQuery('Quy định về bảo đảm thực hiện dự án đầu tư (Ký quỹ đầu tư) theo Luật Đầu tư 2020?', 'DTT')">
                <div class="prompt-card-title">💡 Mức ký quỹ bảo đảm thực hiện dự án đầu tư và các trường hợp được giảm ký quỹ</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Đấu thầu dự án</span>
                  <span style="color: var(--muted);">Điều 43 Luật Đầu tư 2020</span>
                </div>
              </div>

              <!-- NHÓM 7: ĐỊNH GIÁ ĐẤT & TÀI CHÍNH -->
              <div class="prompt-card-item" data-category="TC" onclick="setQuery('Phương pháp thặng dư xác định giá đất cụ thể tính tiền sử dụng đất dự án khu đô thị theo Nghị định 71/2024/NĐ-CP?', 'TC')">
                <div class="prompt-card-title">💡 Áp dụng phương pháp thặng dư tính tiền sử dụng đất dự án BĐS phát triển</div>
                <div class="prompt-card-meta">
                  <span class="prompt-badge">Định giá & Tài chính</span>
                  <span style="color: var(--muted);">Nghị định 71/2024/NĐ-CP</span>
                </div>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>Lĩnh vực pháp lý chuyên ngành</label>
            <select id="projectType" style="max-width: 420px;">
              <option value="Chung">Chung / Tất cả các lĩnh vực pháp lý</option>
              <option value="KĐT">1. Khu đô thị & Bất động sản thương mại</option>
              <option value="NOXH">2. Nhà ở & Nhà ở xã hội</option>
              <option value="NLTT">3. Năng lượng tái tạo & Điện lực</option>
              <option value="ND">4. Bất động sản nghỉ dưỡng & Khách sạn</option>
              <option value="CCN">5. Cụm công nghiệp & Hạ tầng kỹ thuật</option>
              <option value="DTT">6. Đấu thầu & Lựa chọn nhà đầu tư dự án</option>
              <option value="TC">7. Tài chính đất đai & Định giá đất</option>
            </select>
          </div>

          <div class="form-group">
            <label>Nội dung câu hỏi tra cứu</label>
            <textarea id="questionInput" placeholder="Nhập câu hỏi tra cứu luật, nghị định, thông tư (Ví dụ: Quy định bồi thường giải phóng mặt bằng...)">Thủ tục bồi thường GPMB khi thu hồi đất quy định như thế nào?</textarea>
          </div>

          <button class="btn-hacom" onclick="submitQuery()">
            <i class="fa-solid fa-paper-plane"></i> Tra cứu ngay
          </button>
        </div>

        <div id="queryLoader" class="loader">
          <div class="spinner"></div>
          <span>Đang truy vấn kho dữ liệu pháp lý & đồ thị tri thức HACOM...</span>
        </div>

        <div id="queryResultCard" class="surface" style="display: none;">
          <div class="surface-title">
            <i class="fa-solid fa-shield-halved" style="color: var(--success);"></i>
            <span>Kết quả phản hồi & trích dẫn nguồn kiểm chứng</span>
          </div>

          <!-- KHUNG CĂN CỨ VĂN BẢN & MỐC THỜI GIAN HIỆU LỰC -->
          <div id="legalBasisBanner" style="background: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid var(--primary); border-radius: 8px; padding: 14px 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-weight: 700; color: #0f172a; font-size: 13.5px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
              <span><i class="fa-solid fa-scale-balanced" style="color: var(--primary);"></i> CĂN CỨ PHÁP LÝ & THỜI ĐIỂM CÓ HIỆU LỰC THI HÀNH:</span>
              <span class="badge badge-green" style="font-size: 11px;"><i class="fa-solid fa-circle-check"></i> Đang có hiệu lực áp dụng</span>
            </div>
            <div id="legalBasisList" style="font-size: 12.5px; color: #334155; line-height: 1.6;"></div>
          </div>

          <div class="result-box">
            <h4 style="color: var(--primary-strong); margin-bottom: 8px; font-size: 14px;">
              <i class="fa-solid fa-robot"></i> Phản hồi từ HACOM Legal AI Engine:
            </h4>
            <div id="aiResponseText"></div>
          </div>

          <div style="margin-top: 10px;">
            <h4 style="font-size: 14px; font-weight: 700; color: #334155;">
              <i class="fa-solid fa-book-bookmark" style="color: var(--accent);"></i> Danh sách văn bản trích dẫn (Verified Sources):
            </h4>
            <div id="citationsList" class="citations-grid"></div>
          </div>
        </div>
      </div>

      <!-- TAB 2: CẢNH BÁO TÁC ĐỘNG LUẬT MỚI -->
      <div id="alertTab" class="tab-content">
        <div class="surface">
          <div class="surface-title">
            <i class="fa-solid fa-bell" style="color: var(--warning);"></i>
            <span>Đánh giá tác động của văn bản pháp luật mới ban hành</span>
          </div>

          <div class="form-group">
            <label>Số hiệu văn bản mới</label>
            <input type="text" id="docNumberInput" value="71/2024/NĐ-CP" placeholder="Ví dụ: 71/2024/NĐ-CP, 50/2024/NĐ-CP, 33/NQ-CP...">
          </div>

          <div class="form-group">
            <label>Tên văn bản / Nghị định mới</label>
            <input type="text" id="docTitleInput" value="Nghị định 71/2024/NĐ-CP quy định về giá đất" placeholder="Ví dụ: Nghị định 71/2024/NĐ-CP về giá đất...">
          </div>

          <div class="form-group">
            <label>Lĩnh vực áp dụng</label>
            <select id="fieldInput" style="max-width: 300px;">
              <option value="Đất đai">Đất đai / Bồi thường GPMB</option>
              <option value="Xây dựng">Xây dựng & Quy hoạch</option>
              <option value="Nhà ở">Nhà ở & NOXH</option>
              <option value="Đầu tư">Đầu tư & Lợi nhuận</option>
            </select>
          </div>

          <button class="btn-hacom" onclick="submitAlertCheck()">
            <i class="fa-solid fa-chart-line"></i> Phân tích tác động dự án
          </button>
        </div>

        <div id="alertLoader" class="loader">
          <div class="spinner"></div>
          <span>Đang rà soát danh mục dự án HACOM Holdings và đối chiếu quy định mới...</span>
        </div>

        <div id="alertResultCard" class="surface" style="display: none;">
          <div class="surface-title" style="justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <i class="fa-solid fa-shield-cat" style="color: var(--primary);"></i>
              <span>Kết quả đánh giá tác động & mức độ rủi ro</span>
            </div>
            <div id="alertSeverityBadge"></div>
          </div>

          <div class="result-box">
            <h4 style="color: var(--primary-strong); margin-bottom: 6px;">
              <i class="fa-solid fa-circle-exclamation"></i> Khuyến nghị hành động cho Tập đoàn HACOM:
            </h4>
            <div id="alertSummaryText"></div>
          </div>

          <div style="margin-top: 10px;">
            <h4 style="font-size: 14px; font-weight: 700; color: #334155; margin-bottom: 8px;">
              <i class="fa-solid fa-building-flag" style="color: var(--warning);"></i> Danh sách dự án HACOM bị ảnh hưởng trực tiếp:
            </h4>
            <div id="affectedProjectsList" style="display: flex; flex-direction: column; gap: 8px;"></div>
          </div>
        </div>
      </div>

      <!-- TAB 3: ĐỒ THỊ TRI THỨC PHÁP LÝ -->
      <div id="graphTab" class="tab-content">
        <div class="surface">
          <div class="surface-title" style="justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <i class="fa-solid fa-network-wired" style="color: var(--primary);"></i>
              <span>Đồ thị tri thức pháp lý (Legal Knowledge Graph)</span>
            </div>
            <button class="chip" onclick="loadGraphData()">🔄 Tải lại đồ thị</button>
          </div>

          <p style="color: var(--muted); font-size: 13px;">
            Đồ thị tri thức tự động quản lý các mối quan hệ hiệu lực pháp lý giữa Luật, Nghị định và Thông tư hướng dẫn thi hành.
          </p>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 12px 0;">
            <div style="background: var(--primary-soft); border: 1px solid #fecdd3; padding: 16px; border-radius: 10px; text-align: center;">
              <div style="font-size: 24px; font-weight: 800; color: var(--primary-strong);" id="statNodes">--</div>
              <div style="font-size: 12px; color: var(--muted); font-weight: 600;">Văn bản pháp luật (Nodes)</div>
            </div>
            <div style="background: var(--accent-soft); border: 1px solid #fde68a; padding: 16px; border-radius: 10px; text-align: center;">
              <div style="font-size: 24px; font-weight: 800; color: var(--warning);" id="statEdges">--</div>
              <div style="font-size: 12px; color: var(--muted); font-weight: 600;">Mối liên kết pháp lý (Edges)</div>
            </div>
            <div style="background: #fef2f2; border: 1px solid #fca5a5; padding: 16px; border-radius: 10px; text-align: center;">
              <div style="font-size: 24px; font-weight: 800; color: #dc2626;" id="statConflicts">--</div>
              <div style="font-size: 12px; color: #991b1b; font-weight: 600;">Xung đột pháp lý (Conflicts)</div>
            </div>
          </div>

          <!-- MỚI: DÁNH SÁCH XUNG ĐỘT PHÁP LÝ & GỢI Ý VĂN BẢN ƯU TIÊN ÁP DỤNG -->
          <div style="background: #fff5f5; border: 1px solid #fca5a5; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
            <h4 style="font-size: 14px; font-weight: 800; color: #991b1b; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
              <i class="fa-solid fa-triangle-exclamation" style="color: #dc2626;"></i>
              <span>🔥 Xử lý xung đột pháp lý & gợi ý văn bản ưu tiên áp dụng (theo Điều 156 Luật BHVBQPPL)</span>
            </h4>
            <p style="font-size: 12px; color: #7f1d1d; margin-bottom: 12px;">
              Tự động phân xử mâu thuẫn giữa các nghị định, thông tư và gợi ý văn bản có hiệu lực pháp lý cao hơn hoặc quy định chuyên ngành áp dụng cho các dự án HACOM Holdings.
            </p>
            <div id="conflictsResolutionList" style="display: flex; flex-direction: column; gap: 12px;"></div>
          </div>

          <div style="background: #f8fafc; border: 1px solid var(--line); border-radius: 8px; padding: 14px; max-height: 400px; overflow-y: auto;">
            <h4 style="font-size: 13px; font-weight: 700; color: var(--primary-strong); margin-bottom: 10px;">📌 Chi tiết mối liên kết pháp lý:</h4>
            <div id="graphEdgesList" style="display: flex; flex-direction: column; gap: 8px;"></div>
          </div>

          <!-- BẢNG PHÂN XỬ PHỦ QUYẾT ĐIỀU 156 -->
          <div style="margin-top: 20px; border-top: 1px solid var(--line); padding-top: 16px;">
            <div class="surface-title">
              <i class="fa-solid fa-gavel" style="color: var(--primary);"></i>
              <span>Bảng Phân xử Hiệu lực & Phủ quyết Văn bản (Điều 156 Luật Ban hành VBQPPL)</span>
            </div>
            <div style="font-size: 13px; color: var(--muted); margin-bottom: 16px;">
              Nguyên tắc: Văn bản ban hành sau phủ quyết quy định cũ (Khoản 2) • Văn bản cấp cao phủ quyết cấp thấp (Khoản 1) • Quy định chuyên ngành ưu tiên áp dụng (Khoản 3).
            </div>
            <div id="precedenceRulesContainer">
              <div style="text-align: center; color: var(--muted); padding: 10px;">Đang tải danh mục phân xử phủ quyết...</div>
            </div>
          </div>
        </div>
      </div>

      


      <!-- TAB 4: QUẢN LÝ KHO VĂN BẢN PHÁP LUẬT -->
      <div id="uploadTab" class="tab-content">
        <div class="surface">
          <div class="surface-title">
            <i class="fa-solid fa-cloud-arrow-up" style="color: var(--primary);"></i>
            <span>Tải lên & nạp văn bản quy phạm pháp luật mới vào kho AI</span>
          </div>

          <div style="font-size: 13px; color: var(--muted); margin-bottom: 16px;">
            Hệ thống sẽ tự động bóc tách từng Điều/Khoản từ tệp PDF, lập chỉ mục Vector Store và cập nhật vào Đồ thị Tri thức để sẵn sàng tra cứu ngay tức thì.
          </div>

          <!-- DRAG & DROP ZONE -->
          <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
            <i class="fa-solid fa-file-pdf" style="font-size: 42px; color: var(--primary); margin-bottom: 10px;"></i>
            <div style="font-weight: 700; font-size: 14px; color: #1e293b;">Kéo & thả tệp PDF văn bản luật vào đây, hoặc <span style="color: var(--primary); text-decoration: underline;">chọn tệp từ máy tính</span></div>
            <div style="font-size: 12px; color: var(--muted); margin-top: 6px;">Hỗ trợ định dạng .pdf (Luật, Nghị định, Thông tư, Quyết định)</div>
            <input type="file" id="fileInput" accept=".pdf" style="display: none;" onchange="handleFileSelected(this.files)">
          </div>

          <!-- FILE PREVIEW CARD -->
          <div class="file-preview-card" id="filePreviewCard">
            <div style="display: flex; align-items: center; gap: 12px;">
              <i class="fa-solid fa-file-circle-check" style="font-size: 28px; color: var(--success);"></i>
              <div>
                <b id="previewFileName" style="font-size: 13px; color: #1e293b;">filename.pdf</b>
                <div id="previewFileSize" style="font-size: 11px; color: var(--muted);">0 KB</div>
              </div>
            </div>
            <button class="chip" style="background: #fee2e2; color: #991b1b;" onclick="removeSelectedFile()">
              <i class="fa-solid fa-xmark"></i> Hủy chọn
            </button>
          </div>

          <!-- METADATA FORM -->
          <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 14px; margin-bottom: 14px;">
            <div class="form-group" style="margin-bottom: 0;">
              <label>Số hiệu văn bản (Ví dụ: 102/2024/NĐ-CP)</label>
              <input type="text" id="uploadDocNum" placeholder="Nhập số hiệu văn bản...">
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <label>Tên văn bản / Trích yếu nội dung</label>
              <input type="text" id="uploadDocTitle" placeholder="Ví dụ: Quy định chi tiết thi hành Luật Đất đai...">
            </div>
          </div>

          <div class="form-group">
            <label>Lĩnh vực chuyên ngành chính của HACOM</label>
            <select id="uploadField" style="max-width: 380px;">
              <option value="Đất đai & GPMB">1. Đất đai & Bồi thường GPMB</option>
              <option value="Nhà ở & NOXH">2. Nhà ở & Nhà ở xã hội</option>
              <option value="Năng lượng tái tạo">3. Năng lượng tái tạo & Điện lực</option>
              <option value="BĐS Nghỉ dưỡng">4. BĐS nghỉ dưỡng & Khách sạn</option>
              <option value="Cụm công nghiệp">5. Cụm công nghiệp & Hạ tầng</option>
              <option value="Đấu thầu dự án">6. Đấu thầu & Lựa chọn nhà đầu tư</option>
              <option value="Tài chính đất đai">7. Tài chính đất đai & Định giá đất</option>
            </select>
          </div>

          <button class="btn-hacom" id="btnUploadSubmit" onclick="submitFileUpload()">
            <i class="fa-solid fa-cloud-arrow-up"></i> Bóc tách & nạp vào kho dữ liệu AI
          </button>
        </div>

        
        <!-- TÍCH HỢP VIETLEX REST API V1 -->
        <div class="vietlex-box">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="font-size: 15px; font-weight: 800; color: #1e3a8a; display: flex; align-items: center; gap: 8px;">
              <i class="fa-solid fa-globe" style="color: #2563eb;"></i>
              Tra cứu & Đồng bộ Trực tuyến từ Kho Pháp luật Quốc gia (Vietlex.vn)
            </div>
            <span class="prompt-badge" style="background: #dbeafe; color: #1d4ed8; border-color: #93c5fd;">
              <i class="fa-solid fa-database"></i> 60.000+ VBQPPL
            </span>
          </div>

          <div style="font-size: 12px; color: var(--muted); margin-bottom: 14px;">
            Tìm kiếm trực tiếp từ Cổng thông tin Chính phủ & VietLex.vn. Bấm <b>"Nạp vào kho AI"</b> để tự động tải PDF, bóc tách từng Điều/Khoản và lập chỉ mục ngay lập tức.
          </div>

          <!-- GỢI Ý TỪ KHÓA TÌM KIẾM VĂN BẢN NGOÀI KHO -->
          <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;">
            <button class="chip" onclick="searchVietlexDirect('Quản lý xây dựng NĐ 15/2021')"><i class="fa-solid fa-building"></i> NĐ 15/2021 Quản lý xây dựng</button>
            <button class="chip" onclick="searchVietlexDirect('PCCC NĐ 50/2024')"><i class="fa-solid fa-fire-extinguisher"></i> NĐ 50/2024 PCCC mới</button>
            <button class="chip" onclick="searchVietlexDirect('Quy chuẩn PCCC QCVN 06:2022')"><i class="fa-solid fa-shield-halved"></i> QCVN 06:2022 An toàn cháy</button>
            <button class="chip" onclick="searchVietlexDirect('Cụm công nghiệp NĐ 32/2024')"><i class="fa-solid fa-industry"></i> NĐ 32/2024 Cụm công nghiệp</button>
            <button class="chip" onclick="searchVietlexDirect('Khu công nghiệp NĐ 35/2022')"><i class="fa-solid fa-warehouse"></i> NĐ 35/2022 Khu công nghiệp</button>
            <button class="chip" onclick="searchVietlexDirect('Quy hoạch điện VIII')"><i class="fa-solid fa-bolt"></i> QĐ 500 & 262 Quy hoạch điện VIII</button>
            <button class="chip" onclick="searchVietlexDirect('Cấp sổ đỏ TT 10/2024')"><i class="fa-solid fa-id-card"></i> TT 10/2024 Cấp Giấy chứng nhận</button>
            <button class="chip" onclick="searchVietlexDirect('Tháo gỡ thị trường BĐS NQ 33')"><i class="fa-solid fa-hand-holding-dollar"></i> NQ 33/NQ-CP Tháo gỡ BĐS</button>
          </div>

          <!-- THANH TÌM KIẾM VIETLEX -->
          <div style="display: flex; gap: 10px;">
            <input type="text" id="vietlexSearchInput" placeholder="Nhập từ khóa hoặc số hiệu văn bản (VD: 100/2024/NĐ-CP, Quy hoạch đô thị...)" style="flex: 1; padding: 10px 14px; border: 1.5px solid #cbd5e1; border-radius: 8px; font-size: 13px;" onkeypress="if(event.key==='Enter') submitVietlexSearch()">
            <button class="btn-hacom" style="background: #2563eb; border-color: #1d4ed8; padding: 10px 20px;" onclick="submitVietlexSearch()">
              <i class="fa-solid fa-magnifying-glass"></i> Tìm trên VietLex
            </button>
          </div>

          <div id="vietlexLoader" class="loader">
            <div class="spinner" style="border-top-color: #2563eb;"></div>
            <span>Đang kết nối & tra cứu trực tiếp từ Vietlex.vn...</span>
          </div>

          <!-- KẾT QUẢ TÌM KIẾM VIETLEX -->
          <div id="vietlexResultsContainer" style="margin-top: 14px;"></div>
        </div>

        <div id="uploadLoader" class="loader">
          <div class="spinner"></div>
          <span>Đang bóc tách từng Điều/Khoản và lập chỉ mục Vector Store...</span>
        </div>

        <!-- DANH SÁCH VĂN BẢN TRONG KHO -->
        <div class="surface">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <div class="surface-title" style="margin-bottom: 0;">
              <i class="fa-solid fa-folder-open" style="color: var(--primary-strong);"></i>
              <span>Danh mục văn bản luật đã nạp trong hệ thống (<span id="totalDocsCount">0</span> văn bản)</span>
            </div>
            <button class="chip" onclick="fetchDocumentsList()">
              <i class="fa-solid fa-rotate-right"></i> Làm mới danh sách
            </button>
          </div>

          <!-- THANH LỌC NHANH VĂN BẢN -->
          <div style="margin-bottom: 12px; display: flex; gap: 10px; align-items: center;">
            <div style="position: relative; flex: 1;">
              <i class="fa-solid fa-filter" style="position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--muted); font-size: 12px;"></i>
              <input type="text" id="filterDocInput" placeholder="Lọc nhanh danh mục theo số hiệu, tên luật, năm ban hành..." style="width: 100%; padding: 8px 12px 8px 34px; border: 1px solid var(--line); border-radius: 8px; font-size: 12px;" oninput="filterDocumentsTable()">
            </div>
          </div>

          <!-- KHUNG CUỘN DANH MỤC VĂN BẢN CỐ ĐỊNH CHIỀU CAO -->
          <div id="documentsTableContainer" style="overflow-x: auto; max-height: 480px; overflow-y: auto; border: 1px solid var(--line); border-radius: 8px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.03);">
            <table class="doc-table" style="margin: 0; width: 100%;">
              <thead style="position: sticky; top: 0; z-index: 10; background: #f8fafc; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
                <tr>
                  <th>Số hiệu</th>
                  <th>Tên văn bản / Trích yếu</th>
                  <th>Thời gian (Ban hành / Hiệu lực)</th>
                  <th>Lĩnh vực</th>
                  <th>Số đoạn luật (Chunks)</th>
                  <th style="text-align: center;">Hành động</th>
                </tr>
              </thead>
              <tbody id="documentsTableBody">
                <tr><td colspan="6" style="text-align: center; color: var(--muted);">Đang tải danh sách...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <footer>
        © 2026 Tập đoàn HACOM Holdings • HACOM Legal Copilot System (Powered by RAG & Knowledge Graph)
      </footer>
    </main>
  </div>

  <script>
    function switchTab(tabId, element) {
      document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

      if (element) {
        element.classList.add('active');
      } else {
        const navBtn = document.querySelector(`.nav-item[onclick*="${tabId}"]`);
        if (navBtn) navBtn.classList.add('active');
      }

      const targetTab = document.getElementById(tabId);
      if (targetTab) targetTab.classList.add('active');

      if (tabId === 'graphTab') {
        loadGraphData();
        fetchPrecedenceRules();
      } else if (tabId === 'uploadTab') {
        fetchDocumentsList();
      }
    }

    function jumpToTab(tabId) {
      switchTab(tabId, null);
    }

    function jumpToRag(question, projType) {
      jumpToTab('queryTab');
      if (question) document.getElementById('questionInput').value = question;
      if (projType) document.getElementById('projectType').value = projType;
      window.scrollTo({ top: 0, behavior: 'smooth' });
      submitQuery();
    }

    function jumpToAlert(docNum, docTitle, field) {
      jumpToTab('alertTab');
      if (docNum) document.getElementById('docNumberInput').value = docNum;
      if (docTitle) document.getElementById('docTitleInput').value = docTitle;
      if (field) document.getElementById('fieldInput').value = field || 'Đất đai';
      window.scrollTo({ top: 0, behavior: 'smooth' });
      submitAlertCheck();
    }

    function jumpToGraph(docNum) {
      jumpToTab('graphTab');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function filterPrompts(category, btnElement) {
      document.querySelectorAll('.prompt-filter-btn').forEach(btn => btn.classList.remove('active'));
      if (btnElement) btnElement.classList.add('active');

      const cards = document.querySelectorAll('.prompt-card-item');
      let firstMatchedCard = null;

      cards.forEach(card => {
        const cardCat = card.getAttribute('data-category');
        if (category === 'all' || cardCat === category) {
          card.style.display = 'flex';
          if (!firstMatchedCard && cardCat === category) {
            firstMatchedCard = card;
          }
        } else {
          card.style.display = 'none';
        }
      });

      if (category !== 'all') {
        const pType = document.getElementById('projectType');
        if (pType) pType.value = category;

        if (firstMatchedCard) {
          firstMatchedCard.click();
        }
      }
    }

    function setQuery(text, proj) {
      const qInput = document.getElementById('questionInput');
      const pType = document.getElementById('projectType');
      if (qInput) qInput.value = text;
      if (pType && proj) pType.value = proj;
      
      if (qInput) {
        qInput.style.borderColor = 'var(--primary)';
        setTimeout(() => { qInput.style.borderColor = ''; }, 600);
      }
    }

    async function fetchHealth() {
      try {
        const res = await fetch('/api/legal/health');
        const data = await res.json();
        const nodeCount = data.knowledge_graph_nodes || 16;
        document.getElementById('sidebarHealthText').innerText = `${(data.indexed_chunks || 1145).toLocaleString()} Chunks / ${nodeCount} Nodes`;
      } catch (e) {
        console.error("Health check failed:", e);
      }
    }
    fetchHealth();
    fetchDocumentsList();
    fetchPrecedenceRules();


    // XỬ LÝ UPLOAD VĂN BẢN PHÁP QUY
    let currentSelectedFile = null;

    const dropZone = document.getElementById('dropZone');
    if (dropZone) {
      ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => { e.preventDefault(); dropZone.classList.add('dragover'); }, false);
      });
      ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); }, false);
      });
      dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files && dt.files.length > 0) {
          handleFileSelected(dt.files);
        }
      });
    }

    function handleFileSelected(files) {
      if (!files || files.length === 0) return;
      const file = files[0];
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert("Vui lòng chọn tệp định dạng .pdf!");
        return;
      }
      currentSelectedFile = file;
      document.getElementById('previewFileName').innerText = file.name;
      document.getElementById('previewFileSize').innerText = (file.size / 1024).toFixed(1) + " KB";
      document.getElementById('filePreviewCard').style.display = 'flex';

      // Tự động đoán số hiệu từ tên file
      const match = file.name.match(/(\d+[-_]\d+[-_][A-Za-z0-9]+)/);
      if (match && !document.getElementById('uploadDocNum').value) {
        document.getElementById('uploadDocNum').value = match[1].replace(/_/g, '-');
      }
      if (!document.getElementById('uploadDocTitle').value) {
        document.getElementById('uploadDocTitle').value = file.name.replace('.pdf', '').replace(/^[0-9]+_/, '');
      }
    }

    function removeSelectedFile() {
      currentSelectedFile = null;
      document.getElementById('fileInput').value = '';
      document.getElementById('filePreviewCard').style.display = 'none';
    }

    async function submitFileUpload() {
      if (!currentSelectedFile) {
        alert("Vui lòng kéo thả hoặc chọn 1 tệp PDF để nạp!");
        return;
      }

      const docNum = document.getElementById('uploadDocNum').value.trim();
      const docTitle = document.getElementById('uploadDocTitle').value.trim();
      const field = document.getElementById('uploadField').value;

      const formData = new FormData();
      formData.append('file', currentSelectedFile);
      if (docNum) formData.append('doc_number', docNum);
      if (docTitle) formData.append('doc_title', docTitle);
      formData.append('field', field);

      document.getElementById('uploadLoader').style.display = 'flex';
      document.getElementById('btnUploadSubmit').disabled = true;

      try {
        const res = await fetch('/api/legal/upload', {
          method: 'POST',
          body: formData
        });
        const result = await res.json();
        document.getElementById('uploadLoader').style.display = 'none';
        document.getElementById('btnUploadSubmit').disabled = false;

        if (result.success) {
          alert(`🎉 Nạp văn bản thành công!\n- Số hiệu: ${result.doc_number}\n- Đã bóc tách: ${result.chunks_count} điều khoản luật.\n- Tổng số chunks trong hệ thống: ${result.total_chunks}`);
          removeSelectedFile();
          document.getElementById('uploadDocNum').value = '';
          document.getElementById('uploadDocTitle').value = '';
          fetchHealth();
          fetchDocumentsList();
        } else {
          alert("Lỗi: " + (result.detail || result.message || "Không thể nạp văn bản."));
        }
      } catch (err) {
        document.getElementById('uploadLoader').style.display = 'none';
        document.getElementById('btnUploadSubmit').disabled = false;
        alert("Lỗi kết nối máy chủ: " + err);
      }
    }



    function openEditModal(docName, docNumber, field, issueDate, effectiveDate) {
      document.getElementById('editOldDocName').value = docName;
      document.getElementById('editDocNumber').value = docNumber;
      document.getElementById('editDocName').value = docName;
      document.getElementById('editDocField').value = field || 'Đất đai & GPMB';
      if (document.getElementById('editDocIssueDate')) document.getElementById('editDocIssueDate').value = issueDate || '';
      if (document.getElementById('editDocEffectiveDate')) document.getElementById('editDocEffectiveDate').value = effectiveDate || '';
      const modal = document.getElementById('editDocModal');
      modal.style.display = 'flex';
    }

    function closeEditModal() {
      document.getElementById('editDocModal').style.display = 'none';
    }

    async function saveEditDocument() {
      const oldDocName = document.getElementById('editOldDocName').value;
      const newDocNumber = document.getElementById('editDocNumber').value.trim();
      const newDocName = document.getElementById('editDocName').value.trim();
      const newField = document.getElementById('editDocField').value;
      const newIssueDate = document.getElementById('editDocIssueDate') ? document.getElementById('editDocIssueDate').value.trim() : '';
      const newEffectiveDate = document.getElementById('editDocEffectiveDate') ? document.getElementById('editDocEffectiveDate').value.trim() : '';

      if (!newDocName) {
        alert("Vui lòng nhập tên văn bản!");
        return;
      }

      try {
        const res = await fetch('/api/legal/document', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            old_doc_name: oldDocName,
            new_doc_number: newDocNumber,
            new_doc_name: newDocName,
            new_field: newField,
            new_issue_date: newIssueDate,
            new_effective_date: newEffectiveDate
          })
        });
        const result = await res.json().catch(() => ({ success: false, detail: "Máy chủ phản hồi không đúng định dạng" }));
        if (result.success) {
          alert(`✅ Đã cập nhật thành công văn bản "${newDocName}" (${result.updated_chunks} điều khoản)!`);
          closeEditModal();
          fetchHealth();
          fetchDocumentsList();
        } else {
          alert("Lỗi: " + (result.detail || "Không thể cập nhật văn bản."));
        }
      } catch (err) {
        alert("Lỗi: " + (err.message || err));
      }
    }

    async function deleteDocument(docName) {
      if (!confirm(`⚠️ Bạn có chắc chắn muốn XÓA văn bản:\n"${docName}"\nkhỏi kho dữ liệu pháp lý của HACOM không?`)) {
        return;
      }
      try {
        const res = await fetch(`/api/legal/document?doc_name=${encodeURIComponent(docName)}`, {
          method: 'DELETE'
        });
        const result = await res.json();
        if (result.success) {
          alert(`🗑️ Đã xóa thành công văn bản "${docName}" (${result.deleted_chunks} điều khoản)!`);
          fetchHealth();
          fetchDocumentsList();
        } else {
          alert("Lỗi: " + (result.detail || "Không thể xóa văn bản."));
        }
      } catch (err) {
        alert("Lỗi kết nối máy chủ: " + err);
      }
    }

    
    function filterDocumentsTable() {
      const q = (document.getElementById('filterDocInput') ? document.getElementById('filterDocInput').value : '').toLowerCase().trim();
      const tbody = document.getElementById('documentsTableBody');
      if (!tbody) return;
      const rows = tbody.getElementsByTagName('tr');
      for (let r of rows) {
        const text = r.innerText.toLowerCase();
        if (!q || text.includes(q)) {
          r.style.display = '';
        } else {
          r.style.display = 'none';
        }
      }
    }

    async function fetchDocumentsList() {
      const tbody = document.getElementById('documentsTableBody');
      if (!tbody) return;
      try {
        const res = await fetch('/api/legal/documents');
        const data = await res.json();
        const docs = data.documents || [];
        document.getElementById('totalDocsCount').innerText = docs.length;

        if (docs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--muted);">Chưa có văn bản nào trong kho.</td></tr>';
          return;
        }

                tbody.innerHTML = docs.map(d => {
          const safeName = (d.doc_name || '').replace(/['"]/g, '');
          const safeNum = (d.doc_number || '').replace(/['"]/g, '');
          const safeField = (d.field || 'Đất đai & GPMB').replace(/['"]/g, '');
          const safeIssue = (d.issue_date || 'Đang cập nhật').replace(/['"]/g, '');
          const safeEff = (d.effective_date || 'Đang cập nhật').replace(/['"]/g, '');
          return `
          <tr>
            <td><b style="color: var(--primary);">${d.doc_number || "---"}</b></td>
            <td><b>${d.doc_name}</b></td>
            <td>
              <div style="font-size: 11px; color: #334155; display: flex; align-items: center; gap: 5px;">
                <i class="fa-regular fa-calendar-check" style="color: #2563eb;"></i> 
                <span>Ban hành: <b>${safeIssue}</b></span>
              </div>
              <div style="font-size: 11px; color: #166534; margin-top: 3px; display: flex; align-items: center; gap: 5px;">
                <i class="fa-solid fa-scale-balanced" style="color: #16a34a;"></i> 
                <span>Hiệu lực: <b>${safeEff}</b></span>
              </div>
            </td>
            <td><span class="prompt-badge">${d.field || "Chung"}</span></td>
            <td><b>${d.chunks_count}</b> điều khoản</td>
            <td style="text-align: center; white-space: nowrap;">
              <button class="chip" style="background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; cursor: pointer; font-weight: 700; padding: 4px 10px; margin-right: 6px;" onclick="openEditModal('${safeName}', '${safeNum}', '${safeField}', '${safeIssue}', '${safeEff}')">
                <i class="fa-solid fa-pen-to-square"></i> Sửa
              </button>
              <button class="chip" style="background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; cursor: pointer; font-weight: 700; padding: 4px 10px;" onclick="deleteDocument('${safeName}')">
                <i class="fa-solid fa-trash"></i> Xóa
              </button>
            </td>
          </tr>
        `;}).join('');
      } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--danger);">Lỗi tải danh sách văn bản.</td></tr>';
      }
    }


    // TÍCH HỢP VIETLEX & PHÂN XỬ ĐIỀU 156
    async function fetchPrecedenceRules() {
      const container = document.getElementById('precedenceRulesContainer');
      if (!container) return;
      try {
        const res = await fetch('/api/legal/precedence-rules');
        const data = await res.json();
        const rules = data.rules || [];

        if (rules.length === 0) {
          container.innerHTML = '<div style="color: var(--muted); text-align: center;">Chưa có quy tắc phân xử.</div>';
          return;
        }

        container.innerHTML = rules.map(r => `
          <div class="precedence-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
              <div>
                <b style="color: #991b1b; font-size: 14px;">${r.newer_name}</b> 
                <span class="prompt-badge" style="background: #fee2e2; color: #991b1b; border-color: #fca5a5;">PHỦ QUYẾT / THAY THẾ</span>
                <span style="color: var(--muted); font-size: 13px; text-decoration: line-through;">${r.older_name}</span>
              </div>
              <span class="badge badge-green" style="font-size: 11px;">Điều 156 Khoản 2</span>
            </div>
            <div style="font-size: 12px; color: #475569; margin-bottom: 4px;">
              <b>⚖️ Cơ sở pháp lý:</b> ${r.legal_basis}
            </div>
            <div style="font-size: 12px; color: #166534; background: #f0fdf4; padding: 6px 10px; border-radius: 6px;">
              <b>💡 Khuyến nghị HACOM:</b> ${r.impact_hacom}
            </div>
          </div>
        `).join('');
      } catch (e) {
        container.innerHTML = '<div style="color: var(--danger); text-align: center;">Lỗi tải bảng phân xử Điều 156.</div>';
      }
    }

    function searchVietlexDirect(keyword) {
      document.getElementById('vietlexSearchInput').value = keyword;
      submitVietlexSearch();
    }

    async function submitVietlexSearch() {
      const q = document.getElementById('vietlexSearchInput').value.trim();
      if (!q) {
        alert("Vui lòng nhập từ khóa tìm kiếm trên VietLex!");
        return;
      }
      const container = document.getElementById('vietlexResultsContainer');
      const loader = document.getElementById('vietlexLoader');
      loader.style.display = 'flex';
      container.innerHTML = '';

      try {
        const res = await fetch(`/api/legal/vietlex/search?q=${encodeURIComponent(q)}&limit=6`);
        const data = await res.json();
        loader.style.display = 'none';

        if (!data.success || !data.results || data.results.length === 0) {
          container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 16px;">Không tìm thấy văn bản phù hợp trên VietLex.</div>';
          return;
        }

        container.innerHTML = `
          <div style="font-size: 12px; font-weight: 700; color: #1e3a8a; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <span>Tìm thấy <b>${data.total}</b> văn bản phù hợp (Hiển thị ${data.results.length} kết quả):</span>
            <span class="badge badge-green" style="font-size: 11px;"><i class="fa-solid fa-cloud-bolt"></i> ${data.source || 'Cổng TTĐT Chính phủ & VietLex'}</span>
          </div>
        ` + data.results.map(item => {
          const safeTitle = (item.title || '').replace(/['"]/g, '');
          const safeNum = (item.soHieu || '').replace(/['"]/g, '');
          const safePdf = item.pdfUrl || '';
          const hasPdf = safePdf && safePdf.length > 5;

          return `
            <div class="vietlex-result-card">
              <div style="flex: 1; margin-right: 16px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px; flex-wrap: wrap;">
                  <b style="color: #2563eb; font-size: 13px;">${item.soHieu || "VBQPPL"}</b>
                  <span class="prompt-badge" style="font-size: 11px;">${item.loai || "Văn bản"}</span>
                  <small style="color: var(--muted);"><i class="fa-regular fa-calendar"></i> Ban hành: ${item.ngayBanHanh || item.nam || ""}</small>
                  ${item.is_in_repository ? 
                    '<span class="badge badge-green" style="font-size: 10px;"><i class="fa-solid fa-check"></i> Đã có trong kho AI</span>' : 
                    '<span class="prompt-badge" style="background: #f0fdf4; color: #15803d; border-color: #86efac; font-size: 10px; font-weight: 700;"><i class="fa-solid fa-plus"></i> Văn bản mới ngoài kho</span>'
                  }
                </div>
                <div style="font-size: 13px; font-weight: 600; color: #1e293b;">${item.title}</div>
                <div style="font-size: 11px; color: var(--muted); margin-top: 4px;">
                  Nguồn: <b>${item.nguon || "Cổng TTĐT Chính phủ"}</b> • Lĩnh vực: ${item.linhVuc || "Chung"}
                </div>
              </div>
              <div>
                ${hasPdf ? `
                  <button class="chip" style="background: #16a34a; color: #ffffff; border: none; font-weight: 700; padding: 8px 14px; cursor: pointer;" onclick="ingestVietlexDoc('${safePdf}', '${safeNum}', '${safeTitle}')">
                    <i class="fa-solid fa-cloud-arrow-down"></i> Nạp vào kho AI
                  </button>
                ` : `
                  <button class="chip" style="background: #f1f5f9; color: var(--muted); border: 1px solid var(--line); font-size: 11px; padding: 6px 10px;" onclick="fillUploadForm('${safeNum}', '${safeTitle}')">
                    <i class="fa-solid fa-file-pen"></i> Điền form nạp
                  </button>
                `}
              </div>
            </div>
          `;
        }).join('');
      } catch (err) {
        loader.style.display = 'none';
        container.innerHTML = `<div style="text-align: center; color: var(--danger); padding: 16px;">Lỗi kết nối VietLex: ${err.message || err}</div>`;
      }
    }

    async function ingestVietlexDoc(pdfUrl, docNumber, docTitle) {
      if (!confirm(`Bạn có muốn tải và nạp tự động văn bản:
[${docNumber}] ${docTitle}
vào kho dữ liệu AI của HACOM không?`)) {
        return;
      }

      const loader = document.getElementById('uploadLoader');
      loader.style.display = 'flex';

      try {
        const res = await fetch('/api/legal/vietlex/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pdf_url: pdfUrl,
            doc_number: docNumber,
            doc_title: docTitle,
            field: document.getElementById('uploadField') ? document.getElementById('uploadField').value : 'Đất đai & GPMB'
          })
        });
        const result = await res.json();
        loader.style.display = 'none';

        if (result.success) {
          alert(`🎉 Nạp thành công từ VietLex!
- Số hiệu: ${result.doc_number}
- Đã bóc tách: ${result.chunks_count} điều khoản.
- Tổng chunks trong kho: ${result.total_chunks}`);
          fetchHealth();
          fetchDocumentsList();
        } else {
          alert("Lỗi: " + (result.detail || result.error || "Không thể nạp từ VietLex."));
        }
      } catch (e) {
        loader.style.display = 'none';
        alert("Lỗi kết nối máy chủ: " + e);
      }
    }

    function fillUploadForm(docNum, docTitle) {
      if (document.getElementById('uploadDocNum')) document.getElementById('uploadDocNum').value = docNum;
      if (document.getElementById('uploadDocTitle')) document.getElementById('uploadDocTitle').value = docTitle;
      alert("Đã điền số hiệu và tên văn bản vào Form. Vui lòng kéo thả tệp PDF của văn bản này để nạp!");
    }

    async function submitQuery() {
      const question = document.getElementById('questionInput').value.trim();
      const projectType = document.getElementById('projectType').value;

      if (!question) {
        alert("Vui lòng nhập câu hỏi tra cứu!");
        return;
      }

      document.getElementById('queryLoader').style.display = 'flex';
      document.getElementById('queryResultCard').style.display = 'none';

      try {
        const res = await fetch('/api/legal/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: question, project_type: projectType })
        });

        const data = await res.json();
        document.getElementById('queryLoader').style.display = 'none';
        const resultCard = document.getElementById('queryResultCard');
        resultCard.style.display = 'flex';
        setTimeout(() => {
          resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);

        document.getElementById('aiResponseText').innerHTML = marked.parse(data.answer || "Không có phản hồi");

        // RENDER KHUNG CĂN CỨ VĂN BẢN & MỐC THỜI GIAN HIỆU LỰC
        const legalBasisList = document.getElementById('legalBasisList');
        if (data.citations && data.citations.length > 0) {
          const uniqueDocs = {};
          data.citations.forEach(c => {
            const key = c.doc_number || c.doc_name || c.citation;
            if (!uniqueDocs[key]) {
              uniqueDocs[key] = {
                title: c.doc_name || c.citation,
                doc_number: c.doc_number || c.citation,
                issue_date: c.issue_date || '01/01/2024',
                effective_date: c.effective_date || '01/08/2024',
                articles: [c.article]
              };
            } else {
              if (c.article && !uniqueDocs[key].articles.includes(c.article)) {
                uniqueDocs[key].articles.push(c.article);
              }
            }
          });

          let basisHtml = '<div style="display: flex; flex-direction: column; gap: 8px;">';
          Object.values(uniqueDocs).forEach((d, idx) => {
            const artsStr = d.articles.filter(a => a && a !== 'Chung').join(', ');
            basisHtml += `
              <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                  <b style="color: #1e3a8a;"><i class="fa-solid fa-file-lines"></i> ${d.title}</b>
                  ${artsStr ? `<span style="color: #64748b; font-size: 11.5px; margin-left: 6px;">(Trích dẫn: <b>${artsStr}</b>)</span>` : ''}
                </div>
                <div style="display: flex; gap: 12px; font-size: 11.5px;">
                  <span style="color: #475569;"><i class="fa-regular fa-calendar"></i> Ban hành: <b>${d.issue_date}</b></span>
                  <span style="color: #15803d; font-weight: 700;"><i class="fa-solid fa-scale-balanced"></i> Hiệu lực từ: <b>${d.effective_date}</b></span>
                </div>
              </div>
            `;
          });
          basisHtml += '</div>';
          legalBasisList.innerHTML = basisHtml;
        } else {
          legalBasisList.innerHTML = '<span style="color: var(--muted);">Dựa trên các quy định pháp luật hiện hành và dữ liệu tri thức pháp lý HACOM.</span>';
        }

        const citationsList = document.getElementById('citationsList');
        citationsList.innerHTML = '';
        if (data.citations && data.citations.length > 0) {
          data.citations.forEach((c, idx) => {
            const citeTitle = c.citation || c.doc_name || "Trích dẫn pháp lý";
            const articleText = c.article || "Quy định liên quan";
            const fileName = c.doc_name || c.file || "Văn bản PDF";
            const rawContent = c.content || "Nội dung chi tiết quy định theo văn bản pháp luật.";
            const formattedContent = typeof marked !== 'undefined' ? marked.parse(rawContent) : rawContent;
            const issueDate = c.issue_date || "Đang cập nhật";
            const effectiveDate = c.effective_date || "01/08/2024";

            citationsList.innerHTML += `
              <div class="citation-card">
                <div class="citation-title"><i class="fa-solid fa-file-pdf"></i> ${citeTitle}</div>
                <div class="citation-art"><i class="fa-solid fa-bookmark"></i> ${articleText}</div>
                
                <!-- THỜI GIAN BAN HÀNH & HIỆU LỰC THI HÀNH -->
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 10px; margin: 8px 0; font-size: 11.5px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                  <span style="color: #475569;"><i class="fa-regular fa-calendar-check" style="color: #2563eb;"></i> Ban hành: <b>${issueDate}</b></span>
                  <span style="color: #cbd5e1;">|</span>
                  <span style="color: #15803d; font-weight: 700;"><i class="fa-solid fa-scale-balanced" style="color: #16a34a;"></i> Hiệu lực: <b>${effectiveDate}</b></span>
                  <span class="badge badge-green" style="font-size: 10px; margin-left: auto;">🟢 Đang hiệu lực</span>
                </div>

                <div class="citation-file">Tệp nguồn: ${fileName}</div>
                
                <!-- LIÊN KẾT TƯƠNG TÁC SANG TAB 2 VÀ TAB 3 -->
                <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px;">
                  <button class="chip" style="font-size: 11px; padding: 2px 8px;" onclick="jumpToAlert('${citeTitle}', '${fileName}', 'Đất đai')">
                    🚨 Cảnh báo tác động dự án
                  </button>
                  <button class="chip" style="font-size: 11px; padding: 2px 8px;" onclick="jumpToGraph()">
                    🕸️ Xem đồ thị tri thức
                  </button>
                </div>

                <details style="margin-top: 10px; font-size: 12px; border-top: 1px dashed #cbd5e1; padding-top: 8px;">
                  <summary style="cursor: pointer; font-weight: 700; color: var(--primary); outline: none; user-select: none;">
                    🔍 Xem toàn văn nội dung ${articleText}
                  </summary>
                  <div style="background: #ffffff; border: 1px solid #e2e8f0; padding: 12px 14px; border-radius: 8px; margin-top: 8px; font-size: 12px; line-height: 1.7; color: #334155; max-height: 280px; overflow-y: auto; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);">
                    ${formattedContent}
                  </div>
                </details>
              </div>
            `;
          });
        } else {
          citationsList.innerHTML = '<div style="color: var(--muted);">Không tìm thấy trích dẫn cụ thể.</div>';
        }
      } catch (e) {
        document.getElementById('queryLoader').style.display = 'none';
        alert("Lỗi khi gửi yêu cầu tra cứu: " + e.message);
      }
    }

    
    function fillAlertForm(docNum, docTitle, field) {
      document.getElementById('docNumberInput').value = docNum;
      document.getElementById('docTitleInput').value = docTitle;
      document.getElementById('fieldInput').value = field;
      submitAlertCheck();
    }

    async function submitAlertCheck() {
      const docNumber = document.getElementById('docNumberInput').value.trim();
      const docTitle = document.getElementById('docTitleInput').value.trim();
      const field = document.getElementById('fieldInput').value;

      document.getElementById('alertLoader').style.display = 'flex';
      document.getElementById('alertResultCard').style.display = 'none';

      try {
        const res = await fetch('/api/legal/alert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ doc_number: docNumber, doc_title: docTitle, field: field })
        });

        const data = await res.json();
        document.getElementById('alertLoader').style.display = 'none';
        document.getElementById('alertResultCard').style.display = 'block';

        const severityBadge = document.getElementById('alertSeverityBadge');
        const sev = data.severity || "🔵 Mức xanh (Thông tin theo dõi)";
        let severityColor = '#2563eb';
        if (sev.includes('🔴') || sev.includes('Đỏ')) {
          severityColor = '#e1262f';
        } else if (sev.includes('🟡') || sev.includes('Vàng')) {
          severityColor = '#f6a623';
        }

        severityBadge.innerHTML = `<span style="background: ${severityColor}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 13px;">${sev}</span>`;

        const recAction = data.recommended_action || data.summary || "Rà soát quy định pháp lý liên quan.";
        document.getElementById('alertSummaryText').innerText = recAction;

        const projList = document.getElementById('affectedProjectsList');
        projList.innerHTML = '';
        if (data.affected_projects && data.affected_projects.length > 0) {
          data.affected_projects.forEach(p => {
            const pName = p.name || p.project_name || "Dự án HACOM";
            const pType = p.type || "Dự án";
            const pStage = p.stage || p.field || "Giai đoạn triển khai";
            projList.innerHTML += `
              <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid ${severityColor}; padding: 12px 14px; border-radius: 6px; font-size: 13px;">
                <div style="font-weight: 700; color: #1e293b;"><i class="fa-solid fa-building"></i> ${pName} (${pType})</div>
                <div style="color: var(--muted); margin-top: 4px;"><strong>Giai đoạn dự án:</strong> ${pStage}</div>
                <div style="color: #0f172a; margin-top: 6px;"><strong>Hành động khuyến nghị:</strong> ${recAction}</div>
                
                <!-- LIÊN KẾT TƯƠNG TÁC SANG TAB 1 VÀ TAB 3 -->
                <div style="display: flex; gap: 8px; margin-top: 10px;">
                  <button class="chip" style="font-size: 11.5px;" onclick="jumpToRag('Thủ tục đền bù GPMB và quy định pháp lý áp dụng cho ${pName}', '${pType}')">
                    🔍 Tra cứu RAG cho dự án này
                  </button>
                  <button class="chip" style="font-size: 11.5px;" onclick="jumpToGraph()">
                    ⚡ Xem xung đột pháp lý & gợi ý áp dụng
                  </button>
                </div>
              </div>
            `;
          });
        } else {
          projList.innerHTML = '<div style="color: var(--muted);">Không có dự án bị ảnh hưởng trực tiếp.</div>';
        }
      } catch (e) {
        document.getElementById('alertLoader').style.display = 'none';
        alert("Lỗi khi đánh giá cảnh báo: " + e.message);
      }
    }

    var currentViewingDoc = null;
    var currentDocChunks = [];

    async function openDocViewer(docIdentifier) {
      if (!docIdentifier) return;
      const modal = document.getElementById('docViewerModal');
      modal.style.display = 'flex';
      
      document.getElementById('viewModalDocNum').innerText = docIdentifier;
      document.getElementById('viewModalDocTitle').innerText = `Đang tải nội dung văn bản: ${docIdentifier}...`;
      document.getElementById('viewModalIssueDate').innerText = '...';
      document.getElementById('viewModalEffDate').innerText = '...';
      document.getElementById('viewModalChunkCount').innerText = '...';
      document.getElementById('modalArticlesContainer').innerHTML = '<div style="text-align: center; color: var(--muted); padding: 30px;"><div class="spinner" style="margin: 0 auto 10px;"></div>Đang tải toàn bộ các Điều/Khoản pháp luật...</div>';

      try {
        const res = await fetch(`/api/legal/document/details?doc_identifier=${encodeURIComponent(docIdentifier)}`);
        const data = await res.json();
        currentViewingDoc = data;
        currentDocChunks = data.chunks || [];

        document.getElementById('viewModalDocNum').innerText = data.doc_number || docIdentifier;
        document.getElementById('viewModalDocTitle').innerText = data.doc_name || docIdentifier;
        document.getElementById('viewModalIssueDate').innerText = data.issue_date || '01/08/2024';
        document.getElementById('viewModalEffDate').innerText = data.effective_date || '01/08/2024';
        document.getElementById('viewModalChunkCount').innerText = `${currentDocChunks.length} điều khoản`;

        renderModalArticles(currentDocChunks);
      } catch (e) {
        document.getElementById('modalArticlesContainer').innerHTML = `<div style="color: #dc2626; padding: 20px;">Lỗi tải văn bản: ${e.message}</div>`;
      }
    }

    function renderModalArticles(chunks) {
      const container = document.getElementById('modalArticlesContainer');
      container.innerHTML = '';
      if (!chunks || chunks.length === 0) {
        container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 20px;">Văn bản này hiện chưa được nạp các điều khoản chi tiết trong kho Vector Store.</div>';
        return;
      }

      chunks.forEach((ch, idx) => {
        const rawContent = ch.content || '';
        const formatted = typeof marked !== 'undefined' ? marked.parse(rawContent) : rawContent;
        container.innerHTML += `
          <div class="article-item-box" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <b style="color: #1e3a8a; font-size: 13.5px;"><i class="fa-solid fa-bookmark" style="color: var(--primary);"></i> ${ch.article || 'Điều ' + (idx+1)}: ${ch.article_title || ''}</b>
              <span style="font-size: 11px; color: #64748b;"><i class="fa-solid fa-scale-balanced"></i> Hiệu lực: ${ch.effective_date || '01/08/2024'}</span>
            </div>
            <div style="font-size: 12.5px; line-height: 1.65; color: #334155; max-height: 220px; overflow-y: auto; background: #ffffff; padding: 10px 12px; border-radius: 6px; border: 1px solid #f1f5f9;">
              ${formatted}
            </div>
          </div>
        `;
      });
    }

    function filterArticlesInModal() {
      const q = (document.getElementById('filterArticleInput').value || '').toLowerCase().trim();
      if (!q) {
        renderModalArticles(currentDocChunks);
        return;
      }
      const filtered = currentDocChunks.filter(ch => {
        return (ch.article || '').toLowerCase().includes(q) ||
               (ch.article_title || '').toLowerCase().includes(q) ||
               (ch.content || '').toLowerCase().includes(q);
      });
      renderModalArticles(filtered);
    }

    function closeDocViewer() {
      document.getElementById('docViewerModal').style.display = 'none';
    }

    function jumpFromModalToRag() {
      if (!currentViewingDoc) return;
      closeDocViewer();
      jumpToRag(`Phân tích các quy định trọng tâm của ${currentViewingDoc.doc_name || currentViewingDoc.doc_number} đối với dự án HACOM`, 'Chung');
    }

    async function loadGraphData() {
      try {
        const res = await fetch('/api/legal/graph');
        const data = await res.json();

        const nodeCount = data.nodes ? Object.keys(data.nodes).length : 0;
        const conflictsList = data.conflicts || [];
        
        document.getElementById('statNodes').innerText = nodeCount;
        document.getElementById('statEdges').innerText = (data.edges ? data.edges.length : 0);
        document.getElementById('statConflicts').innerText = conflictsList.length;

        // Render Conflict Resolution Cards
        const conflictsContainer = document.getElementById('conflictsResolutionList');
        conflictsContainer.innerHTML = '';
        if (conflictsList.length > 0) {
          conflictsList.forEach((c, idx) => {
            conflictsContainer.innerHTML += `
              <div style="background: #ffffff; border: 1px solid #fecdd3; border-radius: 8px; padding: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <div style="font-weight: 800; font-size: 13px; color: #991b1b;">
                    <i class="fa-solid fa-bolt" style="color: #dc2626;"></i> Xung đột ${idx+1}: <span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px;">${c.source}</span> ⚡ <span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px;">${c.target}</span>
                  </div>
                </div>
                <div style="font-size: 12.5px; color: #334155; margin-bottom: 8px; line-height: 1.5;">
                  <strong>Nội dung xung đột:</strong> ${c.desc}
                </div>
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 10px 12px; border-radius: 6px; margin-bottom: 8px;">
                  <div style="color: #166534; font-weight: 800; font-size: 13px; margin-bottom: 4px;">
                    💡 Gợi ý văn bản ưu tiên áp dụng: <span style="text-decoration: underline;">${c.recommended_doc}</span>
                  </div>
                  <div style="color: #15803d; font-size: 12px; line-height: 1.5;">
                    📜 <strong>Căn cứ pháp lý (Điều 156 Luật BHVBQPPL):</strong> ${c.legal_basis}
                  </div>
                </div>
                <div style="font-size: 12px; color: #1e293b; background: #f8fafc; padding: 8px 10px; border-radius: 6px; border-left: 3px solid var(--primary);">
                  🏗️ <strong>Khuyến nghị cho dự án HACOM:</strong> ${c.hacom_recommendation || 'Áp dụng quy định ưu tiên cho công tác thẩm định pháp lý.'}
                </div>

                <!-- LIÊN KẾT TƯƠNG TÁC SANG TAB 1 VÀ TAB 2 -->
                <div style="display: flex; gap: 8px; margin-top: 10px;">
                  <button class="chip" style="font-size: 11.5px;" onclick="jumpToRag('Phân tích mâu thuẫn giữa ${c.source} và ${c.target} và hướng xử lý cho dự án HACOM', 'Chung')">
                    🔍 Hỏi RAG về xung đột này
                  </button>
                  <button class="chip" style="font-size: 11.5px;" onclick="jumpToAlert('${c.source}', '${c.desc}', 'Đất đai')">
                    🚨 Đánh giá tác động văn bản này
                  </button>
                </div>
              </div>
            `;
          });
        } else {
          conflictsContainer.innerHTML = '<div style="color: var(--muted); font-size: 12px;">Chưa ghi nhận xung đột trong đồ thị.</div>';
        }

        // Render Graph Edges
        const edgesList = document.getElementById('graphEdgesList');
        edgesList.innerHTML = '';
        if (data.edges && data.edges.length > 0) {
          data.edges.forEach(edge => {
            let relBg = '#fff1f1';
            let relColor = 'var(--primary)';
            if (edge.relation === 'CONFLICT_WITH') {
              relBg = '#fee2e2';
              relColor = '#dc2626';
            } else if (edge.relation === 'AMENDS') {
              relBg = '#fef3c7';
              relColor = '#d97706';
            }
            edgesList.innerHTML += `
              <div style="background: #ffffff; border: 1px solid #e2e8f0; padding: 10px 14px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; transition: all 0.2s;" onmouseover="this.style.borderColor='var(--primary)'" onmouseout="this.style.borderColor='#e2e8f0'">
                <button class="chip" style="font-size: 12px; font-weight: 700; color: #1e3a8a; background: #eff6ff; border: 1px solid #bfdbfe; cursor: pointer; text-align: left;" onclick="openDocViewer('${edge.source.replace(/'/g, "\'")}')" title="Bấm để xem toàn văn các điều khoản của văn bản này">
                  <i class="fa-solid fa-file-lines" style="color: #2563eb;"></i> ${edge.source} <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 10px; margin-left: 4px;"></i>
                </button>

                <span style="background: ${relBg}; color: ${relColor}; padding: 4px 12px; border-radius: 12px; font-weight: 700; font-size: 11.5px; border: 1px solid ${relColor}33;">
                  ${edge.relation} — ${edge.desc || ''}
                </span>

                <button class="chip" style="font-size: 12px; font-weight: 700; color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; cursor: pointer; text-align: left;" onclick="openDocViewer('${edge.target.replace(/'/g, "\'")}')" title="Bấm để xem toàn văn các điều khoản của văn bản này">
                  <i class="fa-solid fa-file-lines" style="color: #16a34a;"></i> ${edge.target} <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 10px; margin-left: 4px;"></i>
                </button>
              </div>
            `;
          });
        } else {
          edgesList.innerHTML = '<div style="color: var(--muted);">Chưa có mối liên kết trong đồ thị.</div>';
        }
      } catch (e) {
        console.error("Failed to load graph data:", e);
      }
    }
  </script>

  <!-- MODAL CHỈNH SỬA VĂN BẢN PHÁP LUẬT -->
  <div id="editDocModal" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); z-index: 9999; align-items: center; justify-content: center;">
    <div style="background: #ffffff; border-radius: 16px; width: 90%; max-width: 540px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
        <h3 style="font-size: 16px; font-weight: 800; color: #1e293b; display: flex; align-items: center; gap: 8px;">
          <i class="fa-solid fa-pen-to-square" style="color: var(--primary);"></i>
          Chỉnh sửa thông tin văn bản
        </h3>
        <button onclick="closeEditModal()" style="background: none; border: none; font-size: 18px; cursor: pointer; color: var(--muted);">&times;</button>
      </div>

      <input type="hidden" id="editOldDocName">

      <div class="form-group">
        <label>Số hiệu văn bản (Ví dụ: 102/2024/NĐ-CP)</label>
        <input type="text" id="editDocNumber" placeholder="Nhập số hiệu văn bản...">
      </div>

      <div class="form-group">
        <label>Tên văn bản / Trích yếu nội dung</label>
        <input type="text" id="editDocName" placeholder="Nhập tên văn bản...">
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
        <div class="form-group">
          <label>Ngày ban hành (VD: 18/01/2024)</label>
          <input type="text" id="editDocIssueDate" placeholder="dd/mm/yyyy">
        </div>
        <div class="form-group">
          <label>Ngày có hiệu lực (VD: 01/08/2024)</label>
          <input type="text" id="editDocEffectiveDate" placeholder="dd/mm/yyyy">
        </div>
      </div>

      <div class="form-group">
        <label>Lĩnh vực chuyên ngành của HACOM</label>
        <select id="editDocField">
          <option value="Đất đai & GPMB">1. Đất đai & Bồi thường GPMB</option>
          <option value="Nhà ở & NOXH">2. Nhà ở & Nhà ở xã hội</option>
          <option value="Năng lượng tái tạo">3. Năng lượng tái tạo & Điện lực</option>
          <option value="BĐS Nghỉ dưỡng">4. BĐS nghỉ dưỡng & Khách sạn</option>
          <option value="Cụm công nghiệp">5. Cụm công nghiệp & Hạ tầng</option>
          <option value="Đấu thầu dự án">6. Đấu thầu & Lựa chọn nhà đầu tư</option>
          <option value="Tài chính đất đai">7. Tài chính đất đai & Định giá đất</option>
        </select>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
        <button class="chip" style="padding: 8px 16px;" onclick="closeEditModal()">Hủy</button>
        <button class="btn-hacom" style="padding: 8px 20px;" onclick="saveEditDocument()">
          <i class="fa-solid fa-floppy-disk"></i> Lưu thay đổi
        </button>
      </div>
    </div>
  </div>


  <!-- MODAL XEM TOÀN VĂN VĂN BẢN & CÁC ĐIỀU KHOẢN -->
  <div id="docViewerModal" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.55); z-index: 99999; align-items: center; justify-content: center;">
    <div style="background: #ffffff; border-radius: 16px; width: 92%; max-width: 850px; max-height: 90vh; display: flex; flex-direction: column; padding: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.25);">
      
      <!-- HEADER MODAL -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #e2e8f0; padding-bottom: 14px; margin-bottom: 14px;">
        <div>
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span class="badge badge-red" id="viewModalDocNum" style="font-size: 13px; font-weight: 800;"></span>
            <span class="badge badge-green" id="viewModalStatus" style="font-size: 11px;">🟢 Đang hiệu lực</span>
          </div>
          <h3 id="viewModalDocTitle" style="font-size: 16px; font-weight: 800; color: #1e293b; margin: 0; line-height: 1.4;"></h3>
          <div style="font-size: 12px; color: #64748b; margin-top: 6px; display: flex; gap: 14px;">
            <span><i class="fa-regular fa-calendar-check" style="color: #2563eb;"></i> Ban hành: <b id="viewModalIssueDate" style="color: #1e293b;"></b></span>
            <span><i class="fa-solid fa-scale-balanced" style="color: #16a34a;"></i> Hiệu lực từ: <b id="viewModalEffDate" style="color: #15803d;"></b></span>
            <span><i class="fa-solid fa-layer-group" style="color: var(--primary);"></i> Số điều khoản: <b id="viewModalChunkCount" style="color: #1e293b;"></b></span>
          </div>
        </div>
        <button onclick="closeDocViewer()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #94a3b8; line-height: 1; padding: 4px 8px;">&times;</button>
      </div>

      <!-- THANH TÌM KIẾM ĐIỀU KHOẢN TRONG VĂN BẢN -->
      <div style="margin-bottom: 12px; display: flex; gap: 10px;">
        <input type="text" id="filterArticleInput" placeholder="🔍 Lọc nhanh điều khoản (VD: Điều 87, bồi thường, giá đất, tái định cư...)" style="flex: 1; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 12.5px;" oninput="filterArticlesInModal()">
        <button class="chip" onclick="jumpFromModalToRag()" style="background: var(--primary); color: #fff; border: none; padding: 8px 14px; font-weight: 700; cursor: pointer;">
          <i class="fa-solid fa-robot"></i> Hỏi AI về văn bản này
        </button>
      </div>

      <!-- DANH SÁCH CÁC ĐIỀU KHOẢN -->
      <div id="modalArticlesContainer" style="flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding-right: 6px;">
        <div style="text-align: center; color: var(--muted); padding: 20px;">Đang tải nội dung điều khoản...</div>
      </div>
      
      <!-- FOOTER MODAL -->
      <div style="border-top: 1px solid #e2e8f0; padding-top: 12px; margin-top: 12px; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 11.5px; color: #64748b;">Trích xuất có kiểm chứng từ CSDL Pháp luật HACOM Holdings</span>
        <button class="chip" onclick="closeDocViewer()" style="padding: 6px 18px; font-weight: 700;">Đóng</button>
      </div>
    </div>
  </div>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    return HTML_DASHBOARD


@app.post("/api/legal/upload")
async def upload_legal_document(
    file: UploadFile = File(...),
    doc_number: Optional[str] = Form(None),
    doc_title: Optional[str] = Form(None),
    field: Optional[str] = Form("Đất đai"),
    issue_date: Optional[str] = Form(None),
    effective_date: Optional[str] = Form(None)
):
    """API Tải lên và tự động bóc tách, đánh chỉ mục văn bản luật mới."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận định dạng tệp .pdf")

    try:
        from config import UPLOAD_DIR
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        save_path = UPLOAD_DIR / file.filename
        
        # Ghi file vào thư mục lưu trữ vĩnh viễn
        contents = await file.read()
        with open(save_path, "wb") as f:
            f.write(contents)

        # Bóc tách bằng LegalPDFParser
        parser = LegalPDFParser()
        chunks = parser.parse_legal_chunks(save_path)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Không thể bóc tách nội dung từ tệp PDF này.")

        # Chuẩn hóa metadata người dùng nhập
        final_doc_num = doc_number.strip() if doc_number else chunks[0].get("doc_number", file.filename)
        final_doc_title = doc_title.strip() if doc_title else chunks[0].get("doc_name", file.filename)

        for c in chunks:
            if doc_number:
                c["doc_number"] = final_doc_num
            if doc_title:
                c["doc_name"] = final_doc_title
            c["field"] = field

        # Đánh chỉ mục vào Vector Store
        vector_store.add_chunks(chunks)

        # Cập nhật vào Đồ thị Tri thức
        try:
            if hasattr(kg, "add_document_node"):
                kg.add_document_node(final_doc_num, final_doc_title, "Văn bản mới", field)
        except Exception:
            pass

        return {
            "success": True,
            "filename": file.filename,
            "doc_number": final_doc_num,
            "doc_title": final_doc_title,
            "chunks_count": len(chunks),
            "total_chunks": len(vector_store.chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý tệp: {str(e)}")



class DocumentUpdatePayload(BaseModel):
    old_doc_name: str
    new_doc_number: str
    new_doc_name: str
    new_field: str
    new_issue_date: Optional[str] = ""
    new_effective_date: Optional[str] = ""

@app.put("/api/legal/document")
async def update_legal_document(payload: DocumentUpdatePayload):
    """API Cập nhật Số hiệu, Tên văn bản, Lĩnh vực, Ngày ban hành & Ngày hiệu lực."""
    updated_count = vector_store.update_document_metadata(
        payload.old_doc_name,
        payload.new_doc_number,
        payload.new_doc_name,
        payload.new_field,
        payload.new_issue_date or "",
        payload.new_effective_date or ""
    )
    if updated_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản để cập nhật.")
    
    # Cập nhật node trong Đồ thị Tri thức
    try:
        if hasattr(kg, "add_document_node"):
            kg.add_document_node(payload.new_doc_number, payload.new_doc_name, "Văn bản", payload.new_field)
    except Exception:
        pass

    return {
        "success": True,
        "updated_chunks": updated_count,
        "doc_number": payload.new_doc_number,
        "doc_name": payload.new_doc_name,
        "field": payload.new_field
    }

@app.delete("/api/legal/document")
async def delete_legal_document(doc_name: str = Query(...)):
    """API Xóa một văn bản khỏi kho dữ liệu Vector Store và cập nhật chỉ mục."""
    deleted_chunks = vector_store.delete_document(doc_name)
    if deleted_chunks == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản để xóa.")
    return {
        "success": True,
        "deleted_doc": doc_name,
        "deleted_chunks": deleted_chunks,
        "total_chunks": len(vector_store.chunks)
    }

@app.get("/api/legal/document/details")
def get_document_details(doc_identifier: str):
    """Lấy thông tin chi tiết và toàn bộ các Điều/Khoản của một văn bản pháp luật."""
    if not doc_identifier:
        raise HTTPException(status_code=400, detail="Thiếu mã nhận diện văn bản.")
    
    clean_id = doc_identifier.strip().lower()
    
    # 1. Trích xuất (số, năm) chuẩn hóa (VD: 102/2024/NĐ-CP -> 102 và 2024)
    target_num, target_year = "", ""
    m = re.search(r'(\d+)\s*[\/\-_]\s*(\d{4})', clean_id)
    if m:
        target_num, target_year = m.group(1), m.group(2)
        
    matched_chunks = []
    
    for ch in vector_store.chunks:
        src = str(ch.get("source_file", "")).lower()
        dname = str(ch.get("doc_name", "")).lower()
        dnum = str(ch.get("doc_number", "")).lower()
        full_text = f"{src} {dname} {dnum}"

        # 1. Khớp chính xác theo cặp (số, năm)
        if target_num and target_year:
            m_ch = re.search(r'(\d+)\s*[\/\-_]\s*(\d{4})', full_text)
            if m_ch and m_ch.group(1) == target_num and m_ch.group(2) == target_year:
                matched_chunks.append(ch)
                continue
            if f"{target_num}/{target_year}" in full_text or f"{target_num}-{target_year}" in full_text or f"_{target_num}-" in full_text or f"{target_num}_{target_year}" in full_text or (f"_{target_num}_" in full_text and target_year in full_text):
                matched_chunks.append(ch)
                continue

        # 2. Khớp chuỗi trực tiếp
        if clean_id in full_text or full_text in clean_id:
            matched_chunks.append(ch)
            continue
            
    # 3. Fallback tìm kiếm từ khóa tên luật
    if not matched_chunks:
        tokens = [t for t in re.split(r'[\s,\/\-_]+', clean_id) if len(t) > 2 and t not in ['nghị', 'định', 'luật', 'thông', 'tư', 'ndcp', 'qh15', 'qh14']]
        if tokens:
            for ch in vector_store.chunks:
                dname = str(ch.get("doc_name", "")).lower()
                if any(t in dname for t in tokens):
                    matched_chunks.append(ch)

    if not matched_chunks:
        return {
            "found": False,
            "doc_identifier": doc_identifier,
            "doc_number": doc_identifier,
            "doc_name": doc_identifier,
            "issue_date": "01/08/2024",
            "effective_date": "01/08/2024",
            "chunks_count": 0,
            "chunks": []
        }

    first_chunk = matched_chunks[0]
    return {
        "found": True,
        "doc_identifier": doc_identifier,
        "doc_number": first_chunk.get("doc_number", doc_identifier),
        "doc_name": first_chunk.get("doc_name", doc_identifier),
        "issue_date": first_chunk.get("issue_date", "01/08/2024"),
        "effective_date": first_chunk.get("effective_date", "01/08/2024"),
        "chunks_count": len(matched_chunks),
        "chunks": [
            {
                "article": ch.get("article", "Chung"),
                "article_title": ch.get("article_title", ""),
                "content": ch.get("content", ""),
                "issue_date": ch.get("issue_date", "01/08/2024"),
                "effective_date": ch.get("effective_date", "01/08/2024")
            }
            for ch in matched_chunks
        ]
    }


@app.get("/api/legal/documents")
async def get_indexed_documents():
    """Lấy danh sách tất cả các văn bản luật hiện có trong kho dữ liệu kèm ngày ban hành và hiệu lực cụ thể."""
    doc_stats = {}
    for c in vector_store.chunks:
        doc_num = c.get("doc_number") or c.get("source_file") or "Văn bản"
        doc_name = c.get("doc_name") or c.get("source_file") or "Tài liệu luật"
        field = c.get("field", "Đất đai & GPMB")
        issue_date = c.get("issue_date") or "Đang cập nhật"
        effective_date = c.get("effective_date") or "Đang cập nhật"
        if doc_name not in doc_stats:
            doc_stats[doc_name] = {
                "doc_number": doc_num,
                "doc_name": doc_name,
                "field": field,
                "issue_date": issue_date,
                "effective_date": effective_date,
                "chunks_count": 0
            }
        doc_stats[doc_name]["chunks_count"] += 1

    return {
        "total_documents": len(doc_stats),
        "total_chunks": len(vector_store.chunks),
        "documents": list(doc_stats.values())
    }


@app.get("/api/legal/repository-info")
def get_repository_info():
    """Cung cấp thông tin chi tiết về phạm vi, thời điểm cập nhật và quy mô kho dữ liệu HACOM."""
    doc_stats = {}
    for c in vector_store.chunks:
        doc_name = c.get("doc_name") or c.get("source_file") or "Văn bản"
        doc_num = c.get("doc_number") or doc_name
        field = c.get("field", "Đất đai & GPMB")
        if doc_name not in doc_stats:
            doc_stats[doc_name] = {"doc_name": doc_name, "doc_number": doc_num, "field": field, "count": 0}
        doc_stats[doc_name]["count"] += 1

    return {
        "repository_name": "Kho Dữ liệu & Tri thức Quy phạm Pháp luật Tập đoàn HACOM Holdings",
        "update_horizon": "Cập nhật toàn diện đến Tháng 08/2026",
        "last_sync_date": "21/08/2026",
        "total_documents": len(doc_stats),
        "total_indexed_chunks": len(vector_store.chunks),
        "total_knowledge_nodes": len(kg.nodes),
        "precedence_rules_count": len(precedence_engine.get_all_precedence_rules()),
        "key_reforms_covered": [
            "Luật Đất đai 2024 (31/2024/QH15 - Hiệu lực 01/08/2024)",
            "Luật Nhà ở 2023 (27/2023/QH15 - Hiệu lực 01/08/2024)",
            "Luật Kinh doanh BĐS 2023 (29/2023/QH15 - Hiệu lực 01/08/2024)",
            "Luật Đấu thầu 2023 (22/2023/QH15 - Hiệu lực 01/01/2024)",
            "Nghị định 80/2024/NĐ-CP (Cơ chế DPPA Mua bán điện trực tiếp)",
            "Nghị định 102/2024/NĐ-CP (Quy định chi tiết thi hành Luật Đất đai)",
            "Nghị định 71/2024/NĐ-CP & 88/2024/NĐ-CP (Giá đất & Bồi thường GPMB)",
            "Nghị định 100/2024/NĐ-CP & 136/2026/NĐ-CP (Phát triển và nới điều kiện NOXH)",
            "Nghị định 103/2024/NĐ-CP (Tiền sử dụng đất, tiền thuê đất)",
            "Nghị định 115/2024/NĐ-CP (Lựa chọn nhà đầu tư dự án đất)"
        ],
        "business_domains": [
            {"id": "KDT", "name": "1. Đất đai & Bồi thường GPMB", "desc": "Bảng giá đất, giao đất, cho thuê đất, bồi thường tái định cư"},
            {"id": "NOXH", "name": "2. Nhà ở & Nhà ở xã hội (NOXH)", "desc": "Định mức lợi nhuận 10%, ưu đãi 20% thương mại, nới điều kiện người mua"},
            {"id": "NLTT", "name": "3. Năng lượng tái tạo & Cơ chế DPPA", "desc": "Hợp đồng PPA, mua bán điện trực tiếp ngoài EVN, cơ chế mua bán điện trực tiếp DPPA"},
            {"id": "ND", "name": "4. BĐS Nghỉ dưỡng & Condotel", "desc": "Cấp sổ hồng căn hộ du lịch, condotel, shophouse thương mại"},
            {"id": "CCN", "name": "5. Cụm công nghiệp & Hạ tầng kỹ thuật", "desc": "Quy hoạch CCN, đánh giá ĐTM, xử lý nước thải, ưu đãi hạ tầng"},
            {"id": "DTT", "name": "6. Đấu thầu & Lựa chọn nhà đầu tư", "desc": "Tiêu chuẩn M3, đấu giá quyền sử dụng đất, đấu thầu dự án đô thị"},
            {"id": "TC", "name": "7. Tài chính đất đai & Định giá đất", "desc": "4 phương pháp định giá thặng dư/so sánh, miễn giảm tiền sử dụng đất"}
        ]
    }

@app.get("/api/legal/precedence-rules")
def get_precedence_rules():
    """Lấy danh mục các quy tắc phân xử phủ quyết và ưu tiên áp dụng theo Điều 156."""
    return {
        "legal_basis": "Điều 156 Luật Ban hành văn bản quy phạm pháp luật 2015 (sửa đổi, bổ sung 2020)",
        "rules": precedence_engine.get_all_precedence_rules()
    }

@app.get("/api/legal/vietlex/search")
def search_vietlex_online(q: str = Query("đất đai"), linh_vuc: Optional[str] = None, nam: Optional[int] = None, limit: int = 8):
    """Tra cứu trực tiếp từ Kho Pháp luật Quốc gia VietLex.vn."""
    return vietlex_client.search_laws(query=q, linh_vuc=linh_vuc, nam=nam, limit=limit)

class VietlexIngestPayload(BaseModel):
    pdf_url: str
    doc_number: str
    doc_title: str
    field: Optional[str] = "Đất đai & GPMB"

@app.post("/api/legal/vietlex/ingest")
def ingest_from_vietlex(payload: VietlexIngestPayload):
    """Tải PDF trực tiếp từ Vietlex/Chính phủ và nạp tự động vào CSDL HACOM."""
    res = vietlex_client.download_and_ingest(
        pdf_url=payload.pdf_url,
        doc_number=payload.doc_number,
        doc_title=payload.doc_title,
        field=payload.field
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Lỗi nạp văn bản từ VietLex"))
    return res

@app.get("/api/legal/health")
def health_check():
    return {
        "status": "online",
        "system": "HACOM Legal Copilot Engine",
        "indexed_chunks": len(vector_store.chunks),
        "knowledge_graph_nodes": len(kg.nodes)
    }

@app.post("/api/legal/query")
def query_legal(req: LegalQueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống")
    try:
        res = rag_engine.ask_legal(req.question, req.project_type)
        return res
    except Exception as e:
        print(f"[!] Error processing legal query: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý câu hỏi: {str(e)}")

@app.post("/api/legal/alert")
def check_alert(req: AlertRequest):
    res = alert_engine.assess_new_law_impact(req.doc_number, req.doc_title, req.field)
    return res

@app.get("/api/legal/graph")
def get_graph():
    return {
        "nodes": kg.nodes,
        "edges": kg.edges,
        "conflicts": kg.get_conflicts()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8005)
