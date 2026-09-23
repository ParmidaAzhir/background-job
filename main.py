import datetime
import logging

from fastapi import FastAPI
import inngest
import inngest.fast_api


app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


# Inngest client
inngest_client = inngest.Inngest(
    app_id="report-api",
    logger=logging.getLogger("uvicorn"),
)


# Background function
@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context) -> str:
    await ctx.step.sleep(
        "wait-5-seconds",
        datetime.timedelta(seconds=5),
    )

    return "Hello from the background!"


# Makes the Inngest functions available at /api/inngest
inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello],
)