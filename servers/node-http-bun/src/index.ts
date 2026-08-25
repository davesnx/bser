import { createServer } from "node:http";

const server = createServer((request, response) => {
  if (request.method === "GET" && request.url === "/") {
    response.writeHead(200, {
      "content-type": "text/plain",
      "content-length": "13",
    });
    response.end("Hello, World!");
    return;
  }

  response.writeHead(404);
  response.end();
});

server.listen(Number(process.env.PORT ?? 8080), "0.0.0.0");
