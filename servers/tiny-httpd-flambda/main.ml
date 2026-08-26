module Server = Tiny_httpd

let body = "Hello, World!"
let headers = [ ("content-type", "text/plain"); ("content-length", "13") ]

let () =
  let port =
    match Sys.getenv_opt "PORT" with Some value -> int_of_string value | None -> 8080
  in
  let server = Server.create ~enable_logging:false ~addr:"0.0.0.0" ~port () in
  Server.add_route_handler ~meth:`GET server Server.Route.return (fun _request ->
      Server.Response.make_raw ~headers ~code:200 body);
  Server.run_exn server
