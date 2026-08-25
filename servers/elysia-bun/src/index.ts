import { Elysia } from "elysia";

const port = Number(process.env.PORT ?? 8080);

const app = new Elysia()
  .get("/", () => "Hello, World!")
  .listen({ port, hostname: "0.0.0.0" });

console.log(`elysia-bun listening on port ${app.server?.port}`);
