# not using WS anymore

from __future__ import annotations

import json, uuid, hashlib, time, random

from aiohttp import ClientSession
from aiohttp.http import WSMsgType
import asyncio

from ..typing import AsyncResult, Messages
from .base_provider import AsyncGeneratorProvider, format_prompt


models = {
    "samantha": "1e3be7fe89e94a809408b1154a2ee3e1",
    "gpt-3.5-turbo": "8077335db7cd47e29f7de486612cc7fd",
    "gpt-4": "01c8de4fbfc548df903712b0922a4e01",
}


class Myshell(AsyncGeneratorProvider):
    url = "https://app.myshell.ai/chat"
    working               = False
    supports_gpt_35_turbo = True
    supports_gpt_4        = True

    @classmethod
    async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        timeout: int = 90,
        **kwargs
    ) -> AsyncResult:
        if not model:
            bot_id = models["samantha"]
        elif model in models:
            bot_id = models[model]
        else:
            raise ValueError(f"Model are not supported: {model}")
        
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
        visitor_id = generate_visitor_id(user_agent)

        async with ClientSession(
            headers={'User-Agent': user_agent}
        ) as session:
            async with session.ws_connect(
                "wss://api.myshell.ai/ws/?EIO=4&transport=websocket",
                autoping=False,
                timeout=timeout,
                proxy=proxy
            ) as wss:
                # Send and receive hello message
                await wss.receive_str()
                message = json.dumps({"token": None, "visitorId": visitor_id})
                await wss.send_str(f"40/chat,{message}")
                await wss.receive_str()

                # Fix "need_verify_captcha" issue
                await asyncio.sleep(5)

                # Create chat message
                text = format_prompt(messages)
                chat_data = json.dumps(["text_chat",{
                    "reqId": str(uuid.uuid4()),
                    "botUid": bot_id,
                    "sourceFrom": "myshellWebsite",
                    "text": text,
                    **generate_signature(text)
                }])

                # Send chat message
                chat_start = "42/chat,"
                chat_message = f"{chat_start}{chat_data}"
                await wss.send_str(chat_message)

                # Receive messages
                async for message in wss:
                    if message.type != WSMsgType.TEXT:
                        continue
                    # Ping back
                    if message.data == "2":
                        await wss.send_str("3")
                        continue
                    # Is not chat message
                    if not message.data.startswith(chat_start):
                        continue
                    data_type, data = json.loads(message.data[len(chat_start):])
                    if data_type == "text_stream":
                        if data["data"]["text"]:
                            yield data["data"]["text"]
                        elif data["data"]["isFinal"]:
                            break
                    elif data_type in ("message_replied", "need_verify_captcha"):
                        raise RuntimeError(f"Received unexpected message: {data_type}")


    @classmethod
    @property
    def params(cls):
        params = [
            ("model", "str"),
            ("messages", "list[dict[str, str]]"),
            ("stream", "bool"),
        ]
        param = ", ".join([": ".join(p) for p in params])
        return f"g4f.provider.{cls.__name__} supports: ({param})"


def generate_timestamp() -> str:
    return str(
        int(
            str(int(time.time() * 1000))[:-1]
            + str(
                sum(
                    2 * int(digit)
                    if idx % 2 == 0
                    else 3 * int(digit)
                    for idx, digit in enumerate(str(int(time.time() * 1000))[:-1])
                )
                % 10
            )
        )
    )

def generate_signature(text: str):
    timestamp = generate_timestamp()
    version = 'v1.0.0'
    secret = '8@VXGK3kKHr!u2gA' 
    data = f"{version}#{text}#{timestamp}#{secret}"
    signature = hashlib.md5(data.encode()).hexdigest()
    signature = signature[::-1]
    return {
        "signature": signature,
        "timestamp": timestamp,
        "version": version
    }

def xor_hash(B: str):
    r = []
    i = 0
    
    def o(e, t):
        o_val = 0
        for i in range(len(t)):
            o_val |= r[i] << (8 * i)
        return e ^ o_val
    
    for e in range(len(B)):
        t = ord(B[e])
        r.insert(0, 255 & t)
        
        if len(r) >= 4:
            i = o(i, r)
            r = []
    
    if len(r) > 0:
        i = o(i, r)
    
    return hex(i)[2:]

def performance() -> str:
    t = int(time.time() * 1000)
    e = 0
    while t == int(time.time() * 1000):
        e += 1
    return hex(t)[2:] + hex(e)[2:]

def generate_visitor_id(user_agent: str) -> str:
    f = performance()
    r = hex(int(random.random() * (16**16)))[2:-2]
    d = xor_hash(user_agent)
    e = hex(1080 * 1920)[2:]
    return f"{f}-{r}-{d}-{e}-{f}"



# update
# from g4f.requests import StreamSession

# async def main():
#     headers = {
#         'authority': 'api.myshell.ai',
#         'accept': 'application/json',
#         'accept-language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
#         'content-type': 'application/json',
#         'myshell-service-name': 'organics-api',
#         'origin': 'https://app.myshell.ai',
#         'referer': 'https://app.myshell.ai/',
#         'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"macOS"',
#         'sec-fetch-dest': 'empty',
#         'sec-fetch-mode': 'cors',
#         'sec-fetch-site': 'same-site',
#         'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
#         'visitor-id': '18ae8fe5d916d3-0213f29594b17f-18525634-157188-18ae8fe5d916d3',
#     }

#     json_data = {
#         'conversation_scenario': 3,
#         'botId': '4738',
#         'message': 'hi',
#         'messageType': 1,
#     }
    
#     async with StreamSession(headers=headers, impersonate="chrome110") as session:
#         async with session.post(f'https://api.myshell.ai/v1/bot/chat/send_message', 
#                                 json=json_data) as response:
            
#             response.raise_for_status()
#             async for chunk in response.iter_content():
#                 print(chunk.decode("utf-8"))
                    
# import asyncio
# asyncio.run(main())