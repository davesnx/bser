module Server = Tiny_httpd

let body = "Hello, World!"

let headers = [ ("content-type", "text/plain"); ("content-length", "13") ]

let env_int name default =
  match Sys.getenv_opt name with Some value -> int_of_string value | None -> default

let () =
  let port = env_int "PORT" 8080 in
  let thread_count = env_int "BSER_CPU_COUNT" 1 in
  let pool = Moonpool.Ws_pool.create ~num_threads:thread_count () in
  let server =
    Server.create ~enable_logging:false ~addr:"0.0.0.0" ~port
      ~new_thread:(Moonpool.Runner.run_async pool) ()
  in
  Server.add_route_handler ~meth:`GET server Server.Route.return (fun _request ->
      Server.Response.make_raw ~headers ~code:200 body);
  Server.run_exn server
