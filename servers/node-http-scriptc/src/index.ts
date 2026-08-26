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

const configuredPort = process.env.PORT;
const port = configuredPort === undefined ? 8080 : Number(configuredPort);
server.listen(port, "0.0.0.0");
