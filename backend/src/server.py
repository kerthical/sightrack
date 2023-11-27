from aiohttp import web

if __name__ == "__main__":
    app = web.Application()
    app.router.add_get("/", lambda _: web.Response(text="Hello, world!"))
    print("Starting server...")
    web.run_app(app)
