import Fastify from "fastify";

const port = Number(process.env.PORT ?? 8080);
const body = "Hello, World!";
const app = Fastify({ logger: false });

app.get("/", (_request, reply) => {
  reply.header("Content-Type", "text/plain");
  reply.header("Content-Length", String(Buffer.byteLength(body)));
  return body;
});

await app.listen({ port, host: "0.0.0.0" });
console.log(`fastify-bun listening on port ${port}`);
