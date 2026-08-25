const body = "Hello, World!";
const headers = {
  "content-type": "text/plain",
  "content-length": "13",
};
const response = new Response(body, { headers });

Bun.serve({
  port: Number(process.env.PORT ?? 8080),
  hostname: "0.0.0.0",
  development: process.env.NODE_ENV !== "production",
  routes: {
    "/": {
      GET: response,
    },
  },
  fetch: () => new Response("Not Found", { status: 404 }),
});
