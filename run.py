import os
import asyncio
import uvicorn

from app.bot import main as bot_main

PORT = int(os.getenv("PORT", "3000"))


async def run_api():
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(
        run_api(),
        bot_main(),
    )


if __name__ == "__main__":
    asyncio.run(main())
