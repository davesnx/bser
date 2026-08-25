import express from "express";

const port = Number(process.env.PORT ?? 8080);
const body = "Hello, World!";
const app = express();

app.disable("x-powered-by");
app.get("/", (_request, response) => {
  response.status(200);
  response.setHeader("Content-Type", "text/plain");
  response.setHeader("Content-Length", String(Buffer.byteLength(body)));
  response.end(body);
});

app.listen(port, "0.0.0.0", () => {
  console.log(`express-bun listening on port ${port}`);
});
