import datetime
import logging
import uuid
from fastapi import FastAPI, HTTPException
import inngest
import inngest.fast_api

app = FastAPI()
reports = {}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/reports", status_code=202)
async def create_report(data: dict):
    if "topic" not in data or not data["topic"]:
        raise HTTPException(status_code=400, detail="Topic is required")
    report_id = str(uuid.uuid4())

    reports[report_id] = {
        "id": report_id,
        "topic": data["topic"],
        "status": "pending"
    }

    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={
                "id": report_id,
                "topic": data["topic"]
            }
        )
    )

    return {
        "id": report_id,
        "status": "pending"
    }

@app.get("/reports/{report_id}")
def get_report(report_id: str):
    if report_id not in reports:
        raise HTTPException(status_code=404, detail="Report not found")

    return reports[report_id]

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

@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=2,
)
async def make_report(ctx: inngest.Context) -> str:
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]

    await ctx.step.sleep(
        "do-the-slow-work",
        datetime.timedelta(seconds=8),
    )

    def build_report():
        if topic == "fail":
            raise Exception("The report oven is broken!")
        reports[report_id]["status"] = "done"
        reports[report_id]["result"] = f"Report about {topic}"

    await ctx.step.run("build-report", build_report)

    return "Report completed"

# Makes the Inngest functions available at /api/inngest
inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello, make_report],
)