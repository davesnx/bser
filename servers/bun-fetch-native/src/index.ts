const body = "Hello, World!";
const headers = {
  "content-type": "text/plain",
  "content-length": "13",
};
Bun.serve({
  port: Number(process.env.PORT ?? 8080),
  hostname: "0.0.0.0",
  development: process.env.NODE_ENV !== "production",
  fetch: () => new Response(body, { headers }),
});
