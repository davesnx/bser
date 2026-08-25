import { H3, serve } from "h3";

const app = new H3().get(
  "/",
  () =>
    new Response("Hello, World!", {
      headers: {
        "content-type": "text/plain",
        "content-length": "13",
      },
    }),
);

serve(app, {
  port: Number(process.env.PORT ?? 8080),
  hostname: "0.0.0.0",
  silent: true,
});
